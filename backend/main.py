from fastapi import FastAPI, APIRouter
from pydantic import BaseModel
from services.auth_service import AuthService
from repositories.user_repo import UserRepository
from DataBase import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()
router = APIRouter(prefix="/api/auth")

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

# Эндпоинты теперь на router
@router.post("/register")
def register(data: RegisterRequest):
    return auth_service.register(data.email, data.password, data.name)

@router.post("/login")
def login(data: LoginRequest):
    return auth_service.login(data.email, data.password)

# Подключаем router к app
app.include_router(router)

@app.get("/")
def root():
    return {"message": "API работает"}