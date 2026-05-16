# -*- coding: utf-8 -*-
# services/user_skill_service.py
import colorama
from colorama import init, Fore, Style
init(autoreset=True)
from datetime import datetime
from typing import List, Dict, Any
from DataBase import SkillsUser
from repositories.session_repo import SessionRepository
from repositories.skill_repo import SkillRepository
from repositories.skills_user_repo import SkillsUserRepository


class UserSkillService:
    """
    Service for managing user-selected skills for specific sessions
    """
    
    def __init__(self):
        self.session_repo = SessionRepository()
        self.skill_repo = SkillRepository()
        self.skills_user_repo = SkillsUserRepository()
    
    def save_user_skills_for_session(
        self, 
        user_id: int, 
        session_id: int, 
        skill_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Save user's selected skills for a specific session.
        Replaces all existing selections for this session (delete old, add new).
        
        Args:
            user_id: user id
            session_id: session id
            skill_ids: list of skill ids that user selected
        
        Returns:
            Dict with saved skills info
        
        Raises:
            ValueError: if session doesn't belong to user, or branch_type is wrong,
                       or skill_ids don't exist
        """
        
        # step 1: validate session belongs to user
        session_record = self.session_repo.find_by_id(session_id)
        if not session_record:
            raise ValueError(f"Session with id {session_id} not found")
        
        if session_record.user_id != user_id:
            raise ValueError(f"Session {session_id} does not belong to user {user_id}")
        
        if session_record.branch_type != 1:
            raise ValueError(f"Session {session_id} is not a position branch session (branch_type=1)")
        
        # step 2: validate all skill_ids exist
        valid_skills = []
        for skill_id in skill_ids:
            skill = self.skill_repo.find_by_id(skill_id)
            if not skill:
                raise ValueError(f"Skill with id {skill_id} does not exist")
            valid_skills.append(skill)
        
        # step 3: delete old selections for this session
        deleted_count = self.skills_user_repo.delete_by_user_and_session(user_id, session_id)
        
        # step 4: create new selections
        saved_skills = []
        for skill in valid_skills:
            record = SkillsUser(
                user_id=user_id,
                skill_id=skill.id,
                session_id=session_id,
                specified_date=datetime.now()
            )
            saved = self.skills_user_repo.create(record)
            saved_skills.append({
                "record_id": saved.record_id,
                "skill_id": skill.id,
                "skill_name": skill.name,
                "specified_date": saved.specified_date
            })
        
        return {
            "success": True,
            "message": f"Saved {len(saved_skills)} skills for session {session_id}",
            "deleted_count": deleted_count,
            "saved_skills": saved_skills
        }
    
    def get_user_skills_for_session(
        self, 
        user_id: int, 
        session_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get user's selected skills for a specific session
        
        Args:
            user_id: user id
            session_id: session id
        
        Returns:
            List of skills with details (empty list if none)
        
        Raises:
            ValueError: if session doesn't belong to user
        """
        
        # validate session belongs to user
        session_record = self.session_repo.find_by_id(session_id)
        if not session_record:
            raise ValueError(f"Session with id {session_id} not found")
        
        if session_record.user_id != user_id:
            raise ValueError(f"Session {session_id} does not belong to user {user_id}")
        
        # get skills with details
        skills = self.skills_user_repo.find_by_user_and_session_with_details(user_id, session_id)
        
        return skills
    
    def get_user_skill_ids_for_session(
        self, 
        user_id: int, 
        session_id: int
    ) -> List[int]:
        """
        Get just the skill ids (without details) for a session
        
        Args:
            user_id: user id
            session_id: session id
        
        Returns:
            List of skill ids (empty if none)
        """
        
        return self.skills_user_repo.get_skill_ids_by_user_and_session(user_id, session_id)
