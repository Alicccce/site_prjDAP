import sys
import os
from pathlib import Path

# Добавляем корневую папку проекта в пути для импорта
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from DataBase import Session as DBSession, Position, Skill, SkillsPosition
from DataBase import engine, Base
from sqlalchemy.orm import sessionmaker
import json


class DatabaseService:
    """Сервис для сохранения результатов анализа в БД"""

    def __init__(self):
        self.SessionLocal = sessionmaker(bind=engine)

    def get_or_create_position(self, session, position_name: str):
        """Получает или создаёт запись о должности"""
        position = session.query(Position).filter_by(name=position_name).first()
        if not position:
            position = Position(name=position_name)
            session.add(position)
            session.flush()
        return position

    def get_or_create_skill(self, session, skill_name: str):
        """Получает или создаёт запись о навыке"""
        skill = session.query(Skill).filter_by(name=skill_name).first()
        if not skill:
            skill = Skill(name=skill_name)
            session.add(skill)
            session.flush()
        return skill

    def save_analysis_result(self, user_id: int, query: str, branch_type: int,
                             analysis_result: dict, vacancies_count: int):
        """Сохраняет результат анализа в БД"""
        db_session = self.SessionLocal()

        try:
            # 1. Создаём запись в Session
            new_session = DBSession(
                user_id=user_id,
                branch_type=branch_type,
                search_query=query,
                request_time=datetime.now(),
                ai_result=analysis_result
            )
            db_session.add(new_session)
            db_session.flush()

            print(f"📝 Создана сессия #{new_session.id} для запроса '{query}'")

            # 2. Сохраняем навыки
            skills_saved = 0

            for skill_group in analysis_result.get('skills_analysis', []):
                job_title = skill_group.get('job_title', query)
                skills = skill_group.get('skills', [])

                position = self.get_or_create_position(db_session, job_title)

                for skill_info in skills:
                    skill_name = skill_info.get('name')
                    frequency = skill_info.get('frequency', 0)
                    importance_raw = skill_info.get('importance', 'optional')

                    importance = 'important' if importance_raw in ['mandatory', 'recommended'] else 'not_important'

                    skill = self.get_or_create_skill(db_session, skill_name)

                    skills_position = SkillsPosition(
                        session_id=new_session.id,
                        position_id=position.id,
                        skill_id=skill.id,
                        frequency=int(frequency),
                        importance=importance,
                        analysis_date=datetime.now()
                    )
                    db_session.add(skills_position)
                    skills_saved += 1

            db_session.commit()

            print(f"✅ Сохранено {skills_saved} навыков")

            return {
                "success": True,
                "session_id": new_session.id,
                "skills_saved": skills_saved
            }

        except Exception as e:
            db_session.rollback()
            print(f"❌ Ошибка: {e}")
            return {"success": False, "error": str(e)}
        finally:
            db_session.close()


def get_user_id_by_email(email: str):
    """Получает ID пользователя по email"""
    db_session = sessionmaker(bind=engine)()
    try:
        user = db_session.query(User).filter_by(email=email).first()
        return user.id if user else None
    finally:
        db_session.close()


if __name__ == "__main__":
    # Проверяем подключение к БД
    db_service = DatabaseService()
    print("✅ DatabaseService готов к работе")