from fastapi import FastAPI
from pydantic import BaseModel
from services.auth_service import AuthService
from repositories.user_repo import UserRepository
from DataBase import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()

user_repo = UserRepository()
auth_service = AuthService(user_repo)

# Pydantic модели для валидации
class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

@app.get("/")
def root():
    return {"message": "API работает"}

@app.post("/register")
def register(data: RegisterRequest):
    return auth_service.register(data.email, data.password, data.name)

@app.post("/login")
def login(data: LoginRequest):
    return auth_service.login(data.email, data.password)