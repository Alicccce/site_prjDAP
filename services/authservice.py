from core.security import hash_password, verify_password, create_access_token
from DataBase import User

class AuthService:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    def register(self, email, password, name):
        if self.user_repository.find_by_email(email):
            raise ValueError("Пользователь уже существует")

        # дата рег-и в репозитории
        user = User(
            email=email,
            password=hash_password(password),
            name=name
        )

        user = self.user_repository.create(user)

        return {
            "id": user.id,
            "email": user.email,
            "name": user.name
        }

    def login(self, email, password):
        user = self.user_repository.find_by_email(email)

        if not user:
            raise ValueError("Неверный email или пароль")

        if not verify_password(password, user.password):
            raise ValueError("Неверный email или пароль")

        token, expire = create_access_token(user.id)

        return {
            "access_token": token,
            "expires_at": expire,
            "user_id": user.id
        }