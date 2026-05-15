# -*- coding: utf-8 -*-
# main.py

import json as _json
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware

from services.auth_service import AuthService
from services.user_skill_service import UserSkillService
from services.vacancy_analysis_service import VacancyAnalysisService
from services.qwen_service import generate_learning_plan
from services.position_suggest_service import PositionSuggestService
from repositories.user_repo import UserRepository
from repositories.plan_repo import PlanRepository
from core.security import decode_token
from DataBase import Base, engine, SessionLocal, Plan as PlanModel

Base.metadata.create_all(bind=engine)

user_repo = UserRepository()
auth_service = AuthService(user_repo)
user_skill_service = UserSkillService()
analysis_service = VacancyAnalysisService()
position_suggest_service = PositionSuggestService()
plan_repo = PlanRepository()

app = FastAPI(
    title="Vacancy Analysis API",
    description="API for analyzing vacancies and managing user skills",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://site-prjdap-front.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth dependency ──────────────────────────────────────────

_bearer = HTTPBearer(auto_error=False)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> int:
    """Извлекает user_id из JWT токена. Бросает 401 если токен невалидный."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Токен не передан")
    try:
        return decode_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> int:
    """Возвращает user_id из токена или 1 если токена нет (для обратной совместимости)."""
    if not credentials:
        return 1
    try:
        return decode_token(credentials.credentials)
    except ValueError:
        return 1

# ── Pydantic модели ──────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class UserPreferences(BaseModel):
    level: str
    period: str
    timePerDay: str
    paymentType: str

class SkillAnswer(BaseModel):
    skill: str
    status: str

class UserSkillsRequest(BaseModel):
    jobTitle: str
    totalVacancies: int
    mandatory: List[SkillAnswer]
    optional: List[SkillAnswer]

class SaveUserSkillsRequest(BaseModel):
    session_id: int
    skill_ids: List[int]

class SaveUserSkillsResponse(BaseModel):
    success: bool
    message: str
    deleted_count: int
    saved_skills: List[dict]

class AnalyzeByPositionRequest(BaseModel):
    query: str

class AnalyzeByPositionResponse(BaseModel):
    skills: List[dict]
    total_vacancies: int
    message: str

class SkillItem(BaseModel):
    name: str
    frequency: int = 0
    importance: str = "not_important"

class GeneratePlanRequest(BaseModel):
    jobTitle: str
    deficitSkills: List[SkillItem]
    level: str
    period: str
    timePerDay: str
    paymentType: str

class FiltersRequest(BaseModel):
    specialization: Optional[str] = ""
    industry: Optional[str] = ""
    education: Optional[str] = ""
    salaryFrom: Optional[int] = None
    salaryTo: Optional[int] = None
    schedule: Optional[List[str]] = []

class SuggestPositionsRequest(BaseModel):
    filters: FiltersRequest
    user_skills: List[str] = []

# ── Auth ────────────────────────────────────────────────────

@app.post("/api/auth/register")
def register(data: RegisterRequest):
    return auth_service.register(data.email, data.password, data.name)

@app.post("/api/auth/login")
def login(data: LoginRequest):
    return auth_service.login(data.email, data.password)

# ── User profile ─────────────────────────────────────────────

@app.get("/api/user/profile")
def get_profile(user_id: int = Depends(get_current_user)):
    from DataBase import User as UserModel, Session as SessionModel
    db = SessionLocal()
    try:
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        sessions_count = db.query(SessionModel).filter(SessionModel.user_id == user_id).count()
        plans_count = db.query(PlanModel).filter(PlanModel.user_id == user_id).count()
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "registration_date": user.registration_date.isoformat() if user.registration_date else None,
            "sessions_count": sessions_count,
            "plans_count": plans_count,
        }
    finally:
        db.close()

# ── User preferences ────────────────────────────────────────

@app.post("/api/user/preferences")
def save_preferences(prefs: UserPreferences):
    return {"success": True, "message": "Предпочтения сохранены"}

@app.get("/api/user/preferences")
def get_preferences():
    return {"level": "middle", "period": "6 месяцев", "timePerDay": "60", "paymentType": "mixed"}

# ── User skills ─────────────────────────────────────────────

@app.post("/api/user/skills")
def save_skills(skills: UserSkillsRequest):
    return {"success": True, "message": "Навыки сохранены"}

@app.get("/api/user/skills")
def get_skills():
    return {"jobTitle": "", "totalVacancies": 0, "mandatory": [], "optional": []}

@app.post("/api/user/skills/session", response_model=SaveUserSkillsResponse)
async def save_user_skills(request: SaveUserSkillsRequest, user_id: int = Depends(get_optional_user)):
    try:
        result = user_skill_service.save_user_skills_for_session(
            user_id=user_id,
            session_id=request.session_id,
            skill_ids=request.skill_ids
        )
        return SaveUserSkillsResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/user/skills/session")
async def get_user_skills_session(session_id: int, user_id: int = Depends(get_optional_user)):
    try:
        skills = user_skill_service.get_user_skills_for_session(user_id=user_id, session_id=session_id)
        for skill in skills:
            if 'specified_date' in skill and skill['specified_date']:
                skill['specified_date'] = str(skill['specified_date'])
        return {"success": True, "session_id": session_id, "skills": skills, "count": len(skills)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ── Analyze ─────────────────────────────────────────────────

@app.post("/api/analyze/by-position", response_model=AnalyzeByPositionResponse)
async def analyze_by_position(request: AnalyzeByPositionRequest, user_id: int = Depends(get_optional_user)):
    try:
        skills, total_vacancies = analysis_service.analyzeByPosition(
            user_id=user_id,
            position_query=request.query
        )
        return AnalyzeByPositionResponse(
            skills=skills,
            total_vacancies=total_vacancies,
            message=f"Analysis complete. Found {len(skills)} skills."
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=f"hh.ru timeout: {str(e)}")
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Connection error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ── Plan generation + save ───────────────────────────────────

@app.post("/api/plan/generate")
async def generate_plan(request: GeneratePlanRequest, user_id: int = Depends(get_current_user)):
    try:
        deficit_skills = [
            {"name": s.name, "frequency": s.frequency, "importance": s.importance}
            for s in request.deficitSkills
        ]

        plan_data = generate_learning_plan(
            job_title=request.jobTitle,
            deficit_skills=deficit_skills,
            level=request.level,
            period=request.period,
            time_per_day=request.timePerDay,
            payment_type=request.paymentType
        )

        # Сохраняем план в БД
        db = SessionLocal()
        try:
            db_plan = PlanModel(
                user_id=user_id,
                session_id=1,  # временно, пока нет привязки к сессии
                title=plan_data.get("title", f"План: {request.jobTitle}"),
                ai_result=_json.dumps(plan_data, ensure_ascii=False),
            )
            db.add(db_plan)
            db.commit()
            db.refresh(db_plan)
            plan_id = db_plan.id
        except Exception:
            db.rollback()
            plan_id = None
        finally:
            db.close()

        return {"success": True, "plan": plan_data, "plan_id": plan_id}

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации плана: {str(e)}")

# ── Plan history ─────────────────────────────────────────────

@app.get("/api/plan/history")
def get_plan_history(user_id: int = Depends(get_current_user)):
    """Возвращает список всех планов пользователя."""
    db = SessionLocal()
    try:
        plans = db.query(PlanModel).filter(
            PlanModel.user_id == user_id
        ).order_by(PlanModel.created_date.desc()).all()

        return {
            "plans": [
                {
                    "id": p.id,
                    "title": p.title,
                    "created_date": p.created_date.isoformat() if p.created_date else None,
                }
                for p in plans
            ]
        }
    finally:
        db.close()

@app.get("/api/plan/{plan_id}")
def get_plan(plan_id: int, user_id: int = Depends(get_current_user)):
    """Возвращает конкретный план по ID."""
    db = SessionLocal()
    try:
        plan = db.query(PlanModel).filter(
            PlanModel.id == plan_id,
            PlanModel.user_id == user_id
        ).first()
        if not plan:
            raise HTTPException(status_code=404, detail="План не найден")

        plan_data = None
        if plan.ai_result:
            try:
                plan_data = _json.loads(plan.ai_result)
            except Exception:
                pass

        return {
            "id": plan.id,
            "title": plan.title,
            "created_date": plan.created_date.isoformat() if plan.created_date else None,
            "plan": plan_data,
        }
    finally:
        db.close()

# ── Branch 2: Suggest positions ─────────────────────────────

@app.post("/api/analyze/suggest-positions")
async def suggest_positions(request: SuggestPositionsRequest):
    try:
        filters_dict = {
            "specialization": request.filters.specialization or "",
            "industry": request.filters.industry or "",
            "education": request.filters.education or "",
            "salaryFrom": request.filters.salaryFrom,
            "salaryTo": request.filters.salaryTo,
            "schedule": request.filters.schedule or [],
        }
        positions = position_suggest_service.suggest_positions(
            filters=filters_dict,
            user_skills=request.user_skills,
        )
        return {"positions": positions, "message": f"Found {len(positions)} positions"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=f"hh.ru timeout: {str(e)}")
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Connection error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ── Health ───────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "API is running"}

@app.get("/")
def root():
    return {"message": "API работает"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
