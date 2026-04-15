from DataBase import SkillsPosition
from fastapi import HTTPException # вместо ValueError для чёткого отображения при проверке

class SearchService:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    def search(self, position):
        #if self.user_repository.find_by_email(position):
        #    raise HTTPException(status_code=409, detail="Неправильный ввод")

        #user = User(
        #    email=email,
        #    password_hash=hash_password(password),
        #    name=name
        #)

        #user = self.user_repository.create(user)
        
        #return {
        #    "skill": user.id
        #}