# -*- coding: utf-8 -*-
# repositories/skills_position_repo.py
import colorama
from colorama import init, Fore, Style
# Инициализация colorama (автоматически настраивает кодировку)
init(autoreset=True)

from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from repositories.base_repo import BaseRepository
from DataBase import SkillsPosition, Session, Position, Skill


class SkillsPositionRepository(BaseRepository):
    """
    Repository for position-skill analysis results (skills_position table)
    Ensures uniqueness: (session_id, position_id, skill_id) combination is unique
    
    Methods:
        - create(): save single record with duplicate check
        - create_batch(): save multiple records efficiently
        - create_or_update(): create or update existing record
        - find_by_id(), find_by_session(), find_by_position(), find_by_skill()
        - find_by_session_with_details(): get session records with names (JOIN)
        - find_unique(): check if record exists
        - update(): update existing record
        - delete(): delete record by id
        - count_by_session(): get skill count for session
        - get_importance_stats(): get statistics for important/not_important
        - get_top_skills_for_position(): get top N skills by frequency
        - get_skill_ids_by_position(): get list of skill ids
    """
    
    
    def create(self, record: SkillsPosition) -> SkillsPosition:
        """
        Save a single position-skill analysis record
        Checks if (session_id, position_id, skill_id) already exists
        
        Args:
            record: SkillsPosition object to save
        
        Returns:
            Saved object with record_id assigned
        
        Raises:
            ValueError: if record already exists or referenced entities don't exist
        """
        session = self.get_session()
        try:
            # check if referenced entities exist
            if not self._session_exists(session, record.session_id):
                raise ValueError(f"Session with id '{record.session_id}' does not exist")
            
            if not self._position_exists(session, record.position_id):
                raise ValueError(f"Position with id '{record.position_id}' does not exist")
            
            if not self._skill_exists(session, record.skill_id):
                raise ValueError(f"Skill with id '{record.skill_id}' does not exist")
            
            # check uniqueness
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
            
            # set analysis_date if not provided
            if not record.analysis_date:
                record.analysis_date = datetime.now()
            
            # validate frequency range
            if record.frequency is not None:
                record.frequency = max(0, min(100, record.frequency))
            
            # validate importance value
            if record.importance not in ['important', 'not_important']:
                record.importance = 'not_important'
            
            session.add(record)
            session.commit()
            session.refresh(record)
            session.expunge(record)
            return record
            
        except IntegrityError as e:
            session.rollback()
            raise ValueError(f"Database integrity error: {e}")
        finally:
            session.close()
    
    def create_batch(self, records: List[SkillsPosition]) -> List[SkillsPosition]:
        """
        Save multiple records efficiently in a single transaction
        
        Args:
            records: list of SkillsPosition objects to save
        
        Returns:
            List of saved objects with record_ids assigned
        
        Raises:
            ValueError: if any record is invalid or duplicate
        """
        if not records:
            return []
        
        session = self.get_session()
        created_records = []
        
        try:
            # pre-validate all records
            for record in records:
                # set analysis_date if not provided
                if not record.analysis_date:
                    record.analysis_date = datetime.now()
                
                # validate frequency range
                if record.frequency is not None:
                    record.frequency = max(0, min(100, record.frequency))
                
                # validate importance value
                if record.importance not in ['important', 'not_important']:
                    record.importance = 'not_important'
                
                # check if referenced entities exist
                if not self._session_exists(session, record.session_id):
                    raise ValueError(f"Session with id '{record.session_id}' does not exist")
                
                if not self._position_exists(session, record.position_id):
                    raise ValueError(f"Position with id '{record.position_id}' does not exist")
                
                if not self._skill_exists(session, record.skill_id):
                    raise ValueError(f"Skill with id '{record.skill_id}' does not exist")
                
                # check uniqueness for each record
                existing = self.find_unique(
                    record.session_id,
                    record.position_id,
                    record.skill_id
                )
                if existing:
                    raise ValueError(
                        f"Duplicate record: session_id={record.session_id}, "
                        f"position_id={record.position_id}, skill_id={record.skill_id}"
                    )
            
            # bulk save all records
            for record in records:
                session.add(record)
                session.commit()

            for record in records:
                session.refresh(record)
                session.expunge(record)
                created_records.append(record)
            
            return created_records
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def create_or_update(self, record: SkillsPosition) -> Tuple[SkillsPosition, bool]:
        """
        Create new record or update existing one if already exists
        
        Args:
            record: SkillsPosition object to save or update
        
        Returns:
            Tuple (record, created_flag) where created_flag is True if new record was created
        
        Raises:
            ValueError: if referenced entities don't exist
        """
        session = self.get_session()
        try:
            # check if referenced entities exist
            if not self._session_exists(session, record.session_id):
                raise ValueError(f"Session with id '{record.session_id}' does not exist")
            
            if not self._position_exists(session, record.position_id):
                raise ValueError(f"Position with id '{record.position_id}' does not exist")
            
            if not self._skill_exists(session, record.skill_id):
                raise ValueError(f"Skill with id '{record.skill_id}' does not exist")
            
            # check if record exists
            existing = session.query(SkillsPosition).filter(
                SkillsPosition.session_id == record.session_id,
                SkillsPosition.position_id == record.position_id,
                SkillsPosition.skill_id == record.skill_id
            ).first()
            
            if existing:
                # update existing record
                existing.frequency = record.frequency
                existing.importance = record.importance
                existing.analysis_date = datetime.now()
                
                session.commit()
                session.refresh(existing)
                session.expunge(existing)
                return existing, False
            else:
                # create new record
                if not record.analysis_date:
                    record.analysis_date = datetime.now()
                
                # validate values
                if record.frequency is not None:
                    record.frequency = max(0, min(100, record.frequency))
                
                if record.importance not in ['important', 'not_important']:
                    record.importance = 'not_important'
                
                session.add(record)
                session.commit()
                session.refresh(record)
                session.expunge(record)
                return record, True
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    
    def find_by_id(self, record_id: int) -> Optional[SkillsPosition]:
        """Find record by id"""
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
    
    def find_by_session(self, session_id: int) -> List[SkillsPosition]:
        """Find all analysis records for a specific session"""
        session = self.get_session()
        try:
            records = session.query(SkillsPosition).filter(
                SkillsPosition.session_id == session_id
            ).all()
            
            for record in records:
                session.expunge(record)
            return records
        finally:
            session.close()
    
    def find_by_session_with_details(self, session_id: int) -> List[Dict[str, Any]]:
        """
        Find all records for a session with position and skill names (using JOIN)
        Optimized for display to users
        
        Args:
            session_id: session id
        
        Returns:
            List of dicts with full details:
            [
                {
                    "record_id": 1,
                    "position_id": 1,
                    "position_name": "Data Scientist",
                    "skill_id": 1,
                    "skill_name": "Python",
                    "frequency": 95,
                    "importance": "important",
                    "analysis_date": "2024-01-01 12:00:00"
                },
                ...
            ]
        """
        session = self.get_session()
        try:
            results = session.query(
                SkillsPosition.record_id,
                SkillsPosition.session_id,
                SkillsPosition.position_id,
                Position.name.label("position_name"),
                SkillsPosition.skill_id,
                Skill.name.label("skill_name"),
                SkillsPosition.frequency,
                SkillsPosition.importance,
                SkillsPosition.analysis_date
            ).join(
                Position, SkillsPosition.position_id == Position.id
            ).join(
                Skill, SkillsPosition.skill_id == Skill.id
            ).filter(
                SkillsPosition.session_id == session_id
            ).order_by(
                SkillsPosition.frequency.desc()
            ).all()
            
            return [
                {
                    "record_id": r.record_id,
                    "session_id": r.session_id,
                    "position_id": r.position_id,
                    "position_name": r.position_name,
                    "skill_id": r.skill_id,
                    "skill_name": r.skill_name,
                    "frequency": r.frequency,
                    "importance": r.importance,
                    "analysis_date": r.analysis_date
                }
                for r in results
            ]
        finally:
            session.close()
    
    def find_by_position(self, position_id: int) -> List[Dict[str, Any]]:
        """Find all skills required for a specific position (across all sessions)"""
        session = self.get_session()
        try:
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
            
            return [
                {
                    "skill_id": r.skill_id,
                    "skill_name": r.skill_name,
                    "frequency": r.frequency,
                    "importance": r.importance,
                    "analysis_date": r.analysis_date
                }
                for r in results
            ]
        finally:
            session.close()
    
    def find_by_position_with_frequency(self, position_id: int) -> List[Dict[str, Any]]:
        """
        Get all skills for a position with frequency data
        Optimized for generating learning plans
        
        Args:
            position_id: position id
        
        Returns:
            List of skills sorted by frequency (highest first)
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
            ).all()
            
            return [
                {
                    "skill_id": r.skill_id,
                    "skill_name": r.skill_name,
                    "frequency": r.frequency,
                    "importance": r.importance
                }
                for r in results
            ]
        finally:
            session.close()
    
    def find_by_skill(self, skill_id: int) -> List[Dict[str, Any]]:
        """Find all positions that require a specific skill"""
        session = self.get_session()
        try:
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
            
            return [
                {
                    "position_id": r.position_id,
                    "position_name": r.position_name,
                    "frequency": r.frequency,
                    "importance": r.importance,
                    "analysis_date": r.analysis_date
                }
                for r in results
            ]
        finally:
            session.close()
    
    def find_unique(self, session_id: int, position_id: int, skill_id: int) -> Optional[SkillsPosition]:
        """Check if such record already exists"""
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
    
    # методы для аналитики и статистики
    
    def count_by_session(self, session_id: int) -> int:
        """
        Get number of skills found in a session
        
        Args:
            session_id: session id
        
        Returns:
            Count of skills for this session
        """
        session = self.get_session()
        try:
            count = session.query(func.count(SkillsPosition.record_id)).filter(
                SkillsPosition.session_id == session_id
            ).scalar()
            return count or 0
        finally:
            session.close()
    
    def get_importance_stats(self, session_id: int) -> Dict[str, int]:
        """
        Get statistics for important/not_important skills in a session
        
        Args:
            session_id: session id
        
        Returns:
            Dict with counts: {"important": 5, "not_important": 3, "total": 8}
        """
        session = self.get_session()
        try:
            results = session.query(
                SkillsPosition.importance,
                func.count(SkillsPosition.record_id).label("count")
            ).filter(
                SkillsPosition.session_id == session_id
            ).group_by(
                SkillsPosition.importance
            ).all()
            
            stats = {"important": 0, "not_important": 0, "total": 0}
            for importance, count in results:
                if importance == "important":
                    stats["important"] = count
                elif importance == "not_important":
                    stats["not_important"] = count
                stats["total"] += count
            
            return stats
        finally:
            session.close()
    
    def get_top_skills_for_position(self, position_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top N skills for a position sorted by frequency (highest first)"""
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
            
            return [
                {
                    "skill_id": r.skill_id,
                    "skill_name": r.skill_name,
                    "frequency": r.frequency,
                    "importance": r.importance
                }
                for r in results
            ]
        finally:
            session.close()
    
    def get_skill_ids_by_position(self, position_id: int) -> List[int]:
        """Utility method: get list of skill ids for a specific position"""
        session = self.get_session()
        try:
            skill_ids = session.query(SkillsPosition.skill_id).filter(
                SkillsPosition.position_id == position_id
            ).distinct().all()
            
            return [sid[0] for sid in skill_ids]
        finally:
            session.close()
    

            
            #обновление методов
    def update(self, record: SkillsPosition) -> SkillsPosition:
        """Update record (e.g., change frequency or importance)"""
        session = self.get_session()
        try:
            existing = self.find_by_id(record.record_id)
            if not existing:
                raise ValueError(f"SkillsPosition record with id '{record.record_id}' not found")
            
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
    
    
            #удаление методов
    def delete(self, record_id: int) -> bool:
        """Delete record by id"""
        session = self.get_session()
        try:
            record = self.find_by_id(record_id)
            if not record:
                raise ValueError(f"SkillsPosition record with id '{record_id}' not found")
            
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
    
    def delete_by_session(self, session_id: int) -> int:
        """
        Delete all records for a specific session
        
        Args:
            session_id: session id
        
        Returns:
            Number of deleted records
        """
        session = self.get_session()
        try:
            deleted_count = session.query(SkillsPosition).filter(
                SkillsPosition.session_id == session_id
            ).delete()
            session.commit()
            return deleted_count
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    # вспомогательные методы
    
    def _session_exists(self, session, session_id: int) -> bool:
        """Check if session with such id exists"""
        return session.query(Session).filter(Session.id == session_id).first() is not None
    
    def _position_exists(self, session, position_id: int) -> bool:
        """Check if position with such id exists"""
        return session.query(Position).filter(Position.id == position_id).first() is not None
    
    def _skill_exists(self, session, skill_id: int) -> bool:
        """Check if skill with such id exists"""
        return session.query(Skill).filter(Skill.id == skill_id).first() is not None