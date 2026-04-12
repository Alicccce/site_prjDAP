# -*- coding: utf-8 -*-
# repositories/skills_position_repo.py
import colorama
from colorama import init, Fore, Style
# Инициализация colorama (автоматически настраивает кодировку)
init(autoreset=True)

from datetime import datetime
from sqlalchemy.exc import IntegrityError
from repositories.base_repo import BaseRepository
from DataBase import SkillsPosition, Session, Position, Skill

class SkillsPositionRepository(BaseRepository):
    """
    repository for position-skill analysis results (skills_position table)
    ensures uniqueness: (session_id, position_id, skill_id) combination is unique
    """
    
    def create(self, record):
        """
        save a new position-skill analysis record
        checks if record (session_id, position_id, skill_id) already exists
        
        args:
            record (SkillsPosition): SkillsPosition object to save
        
        returns:
            SkillsPosition: saved object with record_id assigned
        
        raises:
            ValueError: if such (session_id, position_id, skill_id) already exists
            ValueError: if session_id, position_id or skill_id do not exist in db
        """
        session = self.get_session()
        try:
            # проверяем, существуют ли связанные объекты
            if not self._session_exists(session, record.session_id):
                raise ValueError(f"Session with id '{record.session_id}' does not exist")
            
            if not self._position_exists(session, record.position_id):
                raise ValueError(f"Position with id '{record.position_id}' does not exist")
            
            if not self._skill_exists(session, record.skill_id):
                raise ValueError(f"Skill with id '{record.skill_id}' does not exist")
            
            # проверка уникальности (программная)
            existing = self.find_unique(
                record.session_id,
                record.position_id,
                record.skill_id
            )
            if existing:
                raise ValueError(
                    f"SkillsPosition record already exists: session_id={record.session_id}, "
                    f"position_id={record.position_id}, skill_id={record.skill_id}"
                )
            
            # если analysis_date не указан, ставим текущее время
            if not record.analysis_date:
                record.analysis_date = datetime.now()
            
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
            SkillsPosition or None: found record or None
        """
        session = self.get_session()
        try:
            record = session.query(SkillsPosition).filter(
                SkillsPosition.record_id == record_id
            ).first()
            
            if record:
                session.expunge(record)
            return record
        finally:
            session.close()
    
    def find_by_session(self, session_id):
        """
        find all analysis records for a specific session
        
        args:
            session_id (int): session id
        
        returns:
            list[SkillsPosition]: list of records (may be empty)
        """
        session = self.get_session()
        try:
            records = session.query(SkillsPosition).filter(
                SkillsPosition.session_id == session_id
            ).all()
            
            # отсоединяем все объекты от сессии
            for record in records:
                session.expunge(record)
            return records
        finally:
            session.close()
    
    def find_by_position(self, position_id):
        """
        find all skills required for a specific position (across all sessions)
        
        args:
            position_id (int): position id
        
        returns:
            list[dict]: list of dicts with skill info and analysis details
            example: [{"skill_id": 1, "skill_name": "Python", "frequency": 85, "importance": "important"}, ...]
        """
        session = self.get_session()
        try:
            # join with skills table to get skill name
            results = session.query(
                Skill.id.label("skill_id"),
                Skill.name.label("skill_name"),
                SkillsPosition.frequency,
                SkillsPosition.importance,
                SkillsPosition.analysis_date
            ).join(
                SkillsPosition, SkillsPosition.skill_id == Skill.id
            ).filter(
                SkillsPosition.position_id == position_id
            ).all()
            
            # convert to list of dicts for easier use
            skills_list = [
                {
                    "skill_id": r.skill_id,
                    "skill_name": r.skill_name,
                    "frequency": r.frequency,
                    "importance": r.importance,
                    "analysis_date": r.analysis_date
                }
                for r in results
            ]
            return skills_list
        finally:
            session.close()
    
    def find_by_skill(self, skill_id):
        """
        find all positions that require a specific skill (across all sessions)
        
        args:
            skill_id (int): skill id
        
        returns:
            list[dict]: list of dicts with position info and analysis details
            example: [{"position_id": 1, "position_name": "Data Scientist", "frequency": 85, "importance": "important"}, ...]
        """
        session = self.get_session()
        try:
            # join with position table to get position name
            results = session.query(
                Position.id.label("position_id"),
                Position.name.label("position_name"),
                SkillsPosition.frequency,
                SkillsPosition.importance,
                SkillsPosition.analysis_date
            ).join(
                SkillsPosition, SkillsPosition.position_id == Position.id
            ).filter(
                SkillsPosition.skill_id == skill_id
            ).all()
            
            # convert to list of dicts for easier use
            positions_list = [
                {
                    "position_id": r.position_id,
                    "position_name": r.position_name,
                    "frequency": r.frequency,
                    "importance": r.importance,
                    "analysis_date": r.analysis_date
                }
                for r in results
            ]
            return positions_list
        finally:
            session.close()
    
    def find_unique(self, session_id, position_id, skill_id):
        """
        check if such record already exists
        
        args:
            session_id (int): session id
            position_id (int): position id
            skill_id (int): skill id
        
        returns:
            SkillsPosition or None: found record or None
        """
        session = self.get_session()
        try:
            record = session.query(SkillsPosition).filter(
                SkillsPosition.session_id == session_id,
                SkillsPosition.position_id == position_id,
                SkillsPosition.skill_id == skill_id
            ).first()
            
            if record:
                session.expunge(record)
            return record
        finally:
            session.close()
    
    def update(self, record):
        """
        update record (e.g., change frequency or importance)
        
        args:
            record (SkillsPosition): SkillsPosition object with updated data
        
        returns:
            SkillsPosition: updated object
        
        raises:
            ValueError: if record with such record_id not found
        """
        session = self.get_session()
        try:
            # проверяем, существует ли запись
            existing = self.find_by_id(record.record_id)
            if not existing:
                raise ValueError(f"SkillsPosition record with id '{record.record_id}' not found")
            
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
                raise ValueError(f"SkillsPosition record with id '{record_id}' not found")
            
            # получаем объект заново в текущей сессии для удаления
            record_to_delete = session.query(SkillsPosition).filter(
                SkillsPosition.record_id == record_id
            ).first()
            
            session.delete(record_to_delete)
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_skill_ids_by_position(self, position_id):
        """
        utility method: get list of skill ids for a specific position
        
        args:
            position_id (int): position id
        
        returns:
            list[int]: list of skill ids (no duplicates)
        """
        session = self.get_session()
        try:
            skill_ids = session.query(SkillsPosition.skill_id).filter(
                SkillsPosition.position_id == position_id
            ).distinct().all()
            
            return [sid[0] for sid in skill_ids]
        finally:
            session.close()
    
    def get_top_skills_for_position(self, position_id, limit=10):
        """
        get top N skills for a position sorted by frequency (highest first)
        
        args:
            position_id (int): position id
            limit (int): max number of skills to return (default 10)
        
        returns:
            list[dict]: list of dicts with skill info sorted by frequency desc
        """
        session = self.get_session()
        try:
            results = session.query(
                Skill.id.label("skill_id"),
                Skill.name.label("skill_name"),
                SkillsPosition.frequency,
                SkillsPosition.importance
            ).join(
                SkillsPosition, SkillsPosition.skill_id == Skill.id
            ).filter(
                SkillsPosition.position_id == position_id
            ).order_by(
                SkillsPosition.frequency.desc()
            ).limit(limit).all()
            
            skills_list = [
                {
                    "skill_id": r.skill_id,
                    "skill_name": r.skill_name,
                    "frequency": r.frequency,
                    "importance": r.importance
                }
                for r in results
            ]
            return skills_list
        finally:
            session.close()
    
    # вспомогательные методы
    
    def _session_exists(self, session, session_id):
        """check if session with such id exists"""
        return session.query(Session).filter(Session.id == session_id).first() is not None
    
    def _position_exists(self, session, position_id):
        """check if position with such id exists"""
        return session.query(Position).filter(Position.id == position_id).first() is not None
    
    def _skill_exists(self, session, skill_id):
        """check if skill with such id exists"""
        return session.query(Skill).filter(Skill.id == skill_id).first() is not None
