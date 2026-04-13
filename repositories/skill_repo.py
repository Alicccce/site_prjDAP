# -*- coding: utf-8 -*-
# repositories/skill_repo.py
import colorama
from colorama import init, Fore, Style
# Инициализация colorama (автоматически настраивает кодировку)
init(autoreset=True)
from sqlalchemy.exc import IntegrityError
from repositories.base_repo import BaseRepository
from DataBase import Skill

class SkillRepository(BaseRepository):
    """
    Repository for skills (table 'skills')
    Ensures unique skill names (case-insensitive by logic)
    """
    
    def create(self, skill):
        """
        Save a new skill
        
        Args:
            skill (Skill): Skill object to save
        
        Returns:
            Skill: saved skill with id assigned
        
        Raises:
            ValueError: if skill with same name already exists
        """
        session = self.get_session()
        try:
            # check if skill with same name exists
            existing = self.find_by_name(skill.name)
            if existing:
                raise ValueError(f"Skill with name '{skill.name}' already exists")
            
            session.add(skill)
            session.commit()
            session.refresh(skill)
            session.expunge(skill)
            return skill
            
        except IntegrityError as e:
            session.rollback()
            raise ValueError(f"Database integrity error: {e}")
        finally:
            session.close()
    
    def find_by_id(self, skill_id):
        """
        Find skill by id
        
        Args:
            skill_id (int): skill id
        
        Returns:
            Skill or None: found skill
        """
        session = self.get_session()
        try:
            skill = session.query(Skill).filter(
                Skill.id == skill_id
            ).first()
            
            if skill:
                session.expunge(skill)
            return skill
        finally:
            session.close()
    
    def find_by_name(self, name):
        """
        Find skill by exact name (case-insensitive in search)
        
        Args:
            name (str): skill name
        
        Returns:
            Skill or None: found skill
        """
        session = self.get_session()
        try:
            from sqlalchemy import func
            skill = session.query(Skill).filter(
                func.lower(Skill.name) == func.lower(name)
            ).first()
            
            if skill:
                session.expunge(skill)
            return skill
        finally:
            session.close()
    
    def find_all(self):
        """
        Get all skills (for admin panel)
        
        Returns:
            list[Skill]: list of all skills
        """
        session = self.get_session()
        try:
            skills = session.query(Skill).order_by(Skill.name).all()
            
            for skill in skills:
                session.expunge(skill)
            return skills
        finally:
            session.close()
    
    def find_or_create(self, name):
        """
        IMPORTANT METHOD: Check if skill exists, if not - create new
        
        Args:
            name (str): skill name
        
        Returns:
            tuple (Skill, bool): (skill object, created flag)
            created flag is True if new record was created, False if existed
        """
        session = self.get_session()
        try:
            from sqlalchemy import func
            
            # try to find existing
            existing = session.query(Skill).filter(
                func.lower(Skill.name) == func.lower(name)
            ).first()
            
            if existing:
                session.expunge(existing)
                return existing, False
            
            # create new skill
            new_skill = Skill(name=name)
            session.add(new_skill)
            session.commit()
            session.refresh(new_skill)
            session.expunge(new_skill)
            return new_skill, True
            
        except IntegrityError as e:
            session.rollback()
            # if duplicate was created by another process, try to find again
            existing = self.find_by_name(name)
            if existing:
                return existing, False
            raise ValueError(f"Failed to create skill: {e}")
        finally:
            session.close()
    
    def update(self, skill):
        """
        Update skill name
        
        Args:
            skill (Skill): skill object with updated data
        
        Returns:
            Skill: updated skill
        """
        session = self.get_session()
        try:
            existing = self.find_by_id(skill.id)
            if not existing:
                raise ValueError(f"Skill with id '{skill.id}' not found")
            
            # check name uniqueness
            name_exists = session.query(Skill).filter(
                Skill.id != skill.id,
                Skill.name == skill.name
            ).first()
            if name_exists:
                raise ValueError(f"Skill with name '{skill.name}' already exists")
            
            merged = session.merge(skill)
            session.commit()
            session.refresh(merged)
            session.expunge(merged)
            return merged
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def delete(self, skill_id):
        """
        Delete skill by id
        
        Args:
            skill_id (int): skill id
        
        Returns:
            bool: True if deleted
        """
        session = self.get_session()
        try:
            skill = self.find_by_id(skill_id)
            if not skill:
                raise ValueError(f"Skill with id '{skill_id}' not found")
            
            to_delete = session.query(Skill).filter(
                Skill.id == skill_id
            ).first()
            
            session.delete(to_delete)
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
