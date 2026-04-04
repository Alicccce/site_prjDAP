from fastapi import FastAPI
from services.auth_service import AuthService
from repositories.user_repository import UserRepository

app = FastAPI()

user_repo = UserRepository()
auth_service = AuthService(user_repo)

@app.post("/register")
def register(email: str, password: str, name: str):
    return auth_service.register(email, password, name)

@app.post("/login")
def login(email: str, password: str):
    return auth_service.login(email, password)