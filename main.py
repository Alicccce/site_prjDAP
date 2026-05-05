# -*- coding: utf-8 -*-
# main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware

# сервисы
from services.auth_service import AuthService
from services.user_skill_service import UserSkillService
from services.vacancy_analysis_service import VacancyAnalysisService
from services.qwen_service import generate_learning_plan
from services.position_suggest_service import PositionSuggestService
from repositories.user_repo import UserRepository
from DataBase import Base, engine

# создание таблиц
Base.metadata.create_all(bind=engine)

# инициализация сервисов
user_repo = UserRepository()
auth_service = AuthService(user_repo)
user_skill_service = UserSkillService()
analysis_service = VacancyAnalysisService()
position_suggest_service = PositionSuggestService()

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

# ── Модели ──────────────────────────────────────────────────

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

# ── Auth ────────────────────────────────────────────────────

@app.post("/api/auth/register")
def register(data: RegisterRequest):
    return auth_service.register(data.email, data.password, data.name)

@app.post("/api/auth/login")
def login(data: LoginRequest):
    return auth_service.login(data.email, data.password)

# ── User preferences ────────────────────────────────────────

@app.post("/api/user/preferences")
def save_preferences(prefs: UserPreferences):
    print(f"Preferences received: {prefs}")
    return {"success": True, "message": "Предпочтения сохранены"}

@app.get("/api/user/preferences")
def get_preferences():
    return {
        "level": "middle",
        "period": "6 месяцев",
        "timePerDay": "60",
        "paymentType": "mixed"
    }

# ── User skills ─────────────────────────────────────────────

@app.post("/api/user/skills")
def save_skills(skills: UserSkillsRequest):
    print(f"Skills received for {skills.jobTitle}")
    return {"success": True, "message": "Навыки сохранены"}

@app.get("/api/user/skills")
def get_skills():
    return {
        "jobTitle": "",
        "totalVacancies": 0,
        "mandatory": [],
        "optional": []
    }

@app.post("/api/user/skills/session", response_model=SaveUserSkillsResponse)
async def save_user_skills(request: SaveUserSkillsRequest, user_id: int = 1):
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
async def get_user_skills_session(session_id: int, user_id: int = 1):
    try:
        skills = user_skill_service.get_user_skills_for_session(
            user_id=user_id,
            session_id=session_id
        )
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
async def analyze_by_position(request: AnalyzeByPositionRequest, user_id: int = 1):
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

# ── Plan generation ─────────────────────────────────────────

@app.post("/api/plan/generate")
async def generate_plan(request: GeneratePlanRequest):
    """
    Генерирует персональный план обучения через Qwen AI.
    Принимает навыки которые пользователь не знает + ответы на вопросы.
    """
    try:
        deficit_skills = [
            {
                "name": s.name,
                "frequency": s.frequency,
                "importance": s.importance
            }
            for s in request.deficitSkills
        ]

        plan = generate_learning_plan(
            job_title=request.jobTitle,
            deficit_skills=deficit_skills,
            level=request.level,
            period=request.period,
            time_per_day=request.timePerDay,
            payment_type=request.paymentType
        )
        return {"success": True, "plan": plan}

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации плана: {str(e)}")

# ── Branch 2: Suggest positions ─────────────────────────────

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
