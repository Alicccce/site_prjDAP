import colorama
from colorama import init, Fore, Style
init(autoreset=True)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware

# сервисы
from services.auth_service import AuthService
from services.user_skill_service import UserSkillService
from services.vacancy_analysis_service import VacancyAnalysisService
from repositories.user_repo import UserRepository
from DataBase import Base, engine

# создание таблиц
Base.metadata.create_all(bind=engine)

# инициализация сервисов
user_repo = UserRepository()
auth_service = AuthService(user_repo)
user_skill_service = UserSkillService()
analysis_service = VacancyAnalysisService()

# создаём приложение FastAPI
app = FastAPI(
    title="Vacancy Analysis API",
    description="API for analyzing vacancies and managing user skills",
    version="1.0.0"
)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://site-prjdap-front.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Модели для авторизации
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

# Модели для работы с сессиями навыков
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



@app.post("/api/auth/register")
def register(data: RegisterRequest):
    """Register a new user"""
    return auth_service.register(data.email, data.password, data.name)

@app.post("/api/auth/login")
def login(data: LoginRequest):
    """Login user"""
    return auth_service.login(data.email, data.password)



@app.post("/api/user/preferences")
def save_preferences(prefs: UserPreferences):
    """Save user preferences"""
    # TODO: сохранить в БД для текущего пользователя
    print(f"Получены предпочтения: {prefs}")
    return {"success": True, "message": "Предпочтения сохранены"}

@app.get("/api/user/preferences")
def get_preferences():
    """Get user preferences"""
    # TODO: загрузить из БД
    return {
        "level": "middle",
        "period": "6 месяцев",
        "timePerDay": "60",
        "paymentType": "mixed"
    }



@app.post("/api/user/skills")
def save_skills(skills: UserSkillsRequest):
    """Save user skills from frontend questionnaire"""
    # TODO: сохранить в БД для текущего пользователя
    print(f"Получены навыки для {skills.jobTitle}:")
    print(f"  Обязательные: {skills.mandatory}")
    print(f"  Необязательные: {skills.optional}")
    return {"success": True, "message": "Навыки сохранены"}

@app.get("/api/user/skills")
def get_skills():
    """Get user skills"""
    # TODO: загрузить из БД
    return {
        "jobTitle": "Data Scientist",
        "totalVacancies": 150,
        "mandatory": [
            {"skill": "Python", "status": "владею"},
            {"skill": "SQL", "status": "не знаю"}
        ],
        "optional": []
    }



@app.post("/api/user/skills/session", response_model=SaveUserSkillsResponse)
async def save_user_skills(request: SaveUserSkillsRequest, user_id: int = 1):
    """
    Save user's selected skills for a specific session.
    Replaces all previous selections for this session.
    """
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
    """
    Get user's selected skills for a specific session.
    """
    try:
        skills = user_skill_service.get_user_skills_for_session(
            user_id=user_id,
            session_id=session_id
        )
        
        # конвертирует datetime в string для JSON
        for skill in skills:
            if 'specified_date' in skill and skill['specified_date']:
                skill['specified_date'] = str(skill['specified_date'])
        
        return {
            "success": True,
            "session_id": session_id,
            "skills": skills,
            "count": len(skills)
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")



@app.post("/api/analyze/by-position", response_model=AnalyzeByPositionResponse)
async def analyze_by_position(request: AnalyzeByPositionRequest, user_id: int = 1):
    """
    Analyze vacancies by position and save results.
    """
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



@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "API is running"}

@app.get("/")
def root():
    return {"message": "API работает"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)