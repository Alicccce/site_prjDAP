from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from services.auth_service import AuthService
from repositories.user_repo import UserRepository
from DataBase import Base, engine
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI()
router = APIRouter(prefix="/api/auth")
user_router = APIRouter(prefix="/api/user")  # ← новый роутер для пользователя

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

user_repo = UserRepository()
auth_service = AuthService(user_repo)

# Pydantic модели
class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

# Модели для блока вопросов
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

# эндпоинты auth
@router.post("/register")
def register(data: RegisterRequest):
    return auth_service.register(data.email, data.password, data.name)

@router.post("/login")
def login(data: LoginRequest):
    return auth_service.login(data.email, data.password)

# эндпоинты user
@user_router.post("/preferences")
def save_preferences(prefs: UserPreferences):
    # TODO: сохранить в БД для текущего пользователя
    print(f"Получены предпочтения: {prefs}")
    return {"success": True, "message": "Предпочтения сохранены"}

@user_router.post("/skills")
def save_skills(skills: UserSkillsRequest):
    # TODO: сохранить в БД для текущего пользователя
    print(f"Получены навыки для {skills.jobTitle}:")
    print(f"  Обязательные: {skills.mandatory}")
    print(f"  Необязательные: {skills.optional}")
    return {"success": True, "message": "Навыки сохранены"}

@user_router.get("/preferences")
def get_preferences():
    # TODO: загрузить из БД
    return {
        "level": "middle",
        "period": "6 месяцев",
        "timePerDay": "60",
        "paymentType": "mixed"
    }

@user_router.get("/skills")
def get_skills():
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

# подключаем роутеры
app.include_router(router)
app.include_router(user_router)

@app.get("/")
def root():
    return {"message": "API работает"}