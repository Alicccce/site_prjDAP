# -*- coding: utf-8 -*-
# repositories/skills_user_repo.py
import colorama
from colorama import init, Fore, Style
# Инициализация colorama (автоматически настраивает кодировку)
init(autoreset=True)
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from repositories.base_repo import BaseRepository
from DataBase import SkillsUser, User, Skill, Session

class SkillsUserRepository(BaseRepository):
    """
    repository for user-skill links (skills_user table)
    ensures uniqueness: one user cannot add the same skill twice within one session
    """
    
    def create(self, record):
        """
        save a new user-skill link
        checks if record (user_id, skill_id, session_id) already exists
        
        args:
            record (SkillsUser): SkillsUser object to save
        
        returns:
            SkillsUser: saved object with record_id assigned
        
        raises:
            ValueError: if record with such user_id, skill_id, session_id already exists
            ValueError: if user_id, skill_id or session_id do not exist in db
        """
        session = self.get_session()
        try:
            # проверяем, существуют ли связанные объекты
            if not self._user_exists(session, record.user_id):
                raise ValueError(f"User with id '{record.user_id}' does not exist")
            
            if not self._skill_exists(session, record.skill_id):
                raise ValueError(f"Skill with id '{record.skill_id}' does not exist")
            
            if not self._session_exists(session, record.session_id):
                raise ValueError(f"Session with id '{record.session_id}' does not exist")
            
            # проверка уникальности (программная)
            existing = self.find_unique(
                record.user_id, 
                record.skill_id, 
                record.session_id
            )
            if existing:
                raise ValueError(
                    f"User skill record already exists: user_id={record.user_id}, "
                    f"skill_id={record.skill_id}, session_id={record.session_id}"
                )
            
            # если specified_date не указан, ставим текущее время
            if not record.specified_date:
                record.specified_date = datetime.now()
            
            # сохраняем запись
            session.add(record)
            session.commit()
            session.refresh(record)
            
            # отсоединяем объект от сессии, чтобы можно было использовать вне
            session.expunge(record)
            return record
            
        except IntegrityError as e:
            session.rollback()
            raise ValueError(f"Database integrity error: {e}")
        finally:
            session.close()
    
    def find_by_id(self, record_id):
        """
        find record by id
        
        args:
            record_id (int): record id
        
        returns:
            SkillsUser or None: found record or None
        """
        session = self.get_session()
        try:
            record = session.query(SkillsUser).filter(
                SkillsUser.record_id == record_id
            ).first()
            
            if record:
                session.expunge(record)
            return record
        finally:
            session.close()
    
    def find_by_user(self, user_id):
        """
        find all user skills (all sessions)
        
        args:
            user_id (int): user id
        
        returns:
            list[SkillsUser]: list of records (may be empty)
        """
        session = self.get_session()
        try:
            records = session.query(SkillsUser).filter(
                SkillsUser.user_id == user_id
            ).all()
            
            # отсоединяем все объекты от сессии
            for record in records:
                session.expunge(record)
            return records
        finally:
            session.close()
    
    def find_by_user_and_session(self, user_id, session_id):
        """
        find all skills that user specified in a specific session
        
        args:
            user_id (int): user id
            session_id (int): search session id
        
        returns:
            list[dict]: list of dicts with skill info
            example: [{"skill_id": 1, "skill_name": "Python", "specified_date": "2024-01-01"}, ...]
        """
        session = self.get_session()
        try:
            # join with skills table to get skill name
            results = session.query(
                Skill.id.label("skill_id"),
                Skill.name.label("skill_name"),
                SkillsUser.specified_date
            ).join(
                SkillsUser, SkillsUser.skill_id == Skill.id
            ).filter(
                SkillsUser.user_id == user_id,
                SkillsUser.session_id == session_id
            ).all()
            
            # convert to list of dicts for easier use
            skills_list = [
                {
                    "skill_id": r.skill_id,
                    "skill_name": r.skill_name,
                    "specified_date": r.specified_date
                }
                for r in results
            ]
            return skills_list
        finally:
            session.close()
    
    def find_unique(self, user_id, skill_id, session_id):
        """
        check if such record already exists
        
        args:
            user_id (int): user id
            skill_id (int): skill id
            session_id (int): session id
        
        returns:
            SkillsUser or None: found record or None
        """
        session = self.get_session()
        try:
            record = session.query(SkillsUser).filter(
                SkillsUser.user_id == user_id,
                SkillsUser.skill_id == skill_id,
                SkillsUser.session_id == session_id
            ).first()
            
            if record:
                session.expunge(record)
            return record
        finally:
            session.close()
    
    def update(self, record):
        """
        update record (e.g., change specified_date)
        
        args:
            record (SkillsUser): SkillsUser object with updated data
        
        returns:
            SkillsUser: updated object
        
        raises:
            ValueError: if record with such record_id not found
        """
        session = self.get_session()
        try:
            # проверяем, существует ли запись
            existing = self.find_by_id(record.record_id)
            if not existing:
                raise ValueError(f"SkillsUser record with id '{record.record_id}' not found")
            
            # обновляем запись
            merged_record = session.merge(record)
            session.commit()
            session.refresh(merged_record)
            session.expunge(merged_record)
            return merged_record
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def delete(self, record_id):
        """
        delete record by id
        
        args:
            record_id (int): record id
        
        returns:
            bool: True if deletion successful
        
        raises:
            ValueError: if record with such id not found
        """
        session = self.get_session()
        try:
            record = self.find_by_id(record_id)
            if not record:
                raise ValueError(f"SkillsUser record with id '{record_id}' not found")
            
            # получаем объект заново в текущей сессии для удаления
            record_to_delete = session.query(SkillsUser).filter(
                SkillsUser.record_id == record_id
            ).first()
            
            session.delete(record_to_delete)
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_skill_names_by_user(self, user_id):
        """
        utility method: get simple list of user skill names
        
        args:
            user_id (int): user id
        
        returns:
            list[str]: list of skill names (no duplicates)
        """
        session = self.get_session()
        try:
            skills = session.query(Skill.name).join(
                SkillsUser, SkillsUser.skill_id == Skill.id
            ).filter(
                SkillsUser.user_id == user_id
            ).distinct().all()
            
            return [skill[0] for skill in skills]
        finally:
            session.close()
    
    # вспомогательные методы
    
    def _user_exists(self, session, user_id):
        """check if user with such id exists"""
        return session.query(User).filter(User.id == user_id).first() is not None
    
    def _skill_exists(self, session, skill_id):
        """check if skill with such id exists"""
        return session.query(Skill).filter(Skill.id == skill_id).first() is not None
    
    def _session_exists(self, session, session_id):
        """check if session with such id exists"""
        return session.query(Session).filter(Session.id == session_id).first() is not None
