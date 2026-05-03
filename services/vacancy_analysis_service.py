# -*- coding: utf-8 -*-
# services/vacancy_analysis_service.py

from datetime import datetime
from typing import List, Dict, Any
from DataBase import Session as DBSession, SkillsPosition
from repositories.session_repo import SessionRepository
from repositories.position_repo import PositionRepository
from repositories.skill_repo import SkillRepository
from repositories.skills_position_repo import SkillsPositionRepository
from services.skill_extractor import extract_skills_from_vacancies, get_position_name
from hh_client import HHClient


class VacancyAnalysisService:
    """
    Service for coordinating position branch analysis:
    from user request to saving results to database.
    Uses deterministic skill extraction (no AI).
    """
    
    def __init__(self):
        self.session_repo = SessionRepository()
        self.position_repo = PositionRepository()
        self.skill_repo = SkillRepository()
        self.skills_position_repo = SkillsPositionRepository()
        self.hh_client = HHClient()
    
    def analyzeByPosition(self, user_id: int, position_query: str) -> List[Dict[str, Any]]:
        """
        Main method: analyze positions by user query
        
        Steps:
        1. Create search session
        2. Fetch vacancies from hh.ru
        3. Send to AI for analysis
        4. Save position (find or create)
        5. Save skills and links (SkillsPosition)
        6. Return result to user
        
        Args:
            user_id (int): user id
            position_query (str): search query (e.g., "Data Scientist")
        
        Returns:
            list[dict]: list of skills with frequency and importance
        
        Raises:
            ValueError: if query is empty
            TimeoutError: if hh.ru doesn't respond
            ConnectionError: if no connection to hh.ru
            RuntimeError: if AI returns empty result
        """
        
        # step 0: validate input
        if not position_query or not position_query.strip():
            raise ValueError("Position query cannot be empty")
        
        # step 1: create search session
        print(f"[Step 1] Creating session for user {user_id}...")
        session_record = DBSession(
            user_id=user_id,
            branch_type=1,  # 1 = position branch
            search_query=position_query,
            request_time=datetime.now()
        )
        created_session = self.session_repo.create(session_record)
        session_id = created_session.id
        print(f"[Step 1] Session created with id={session_id}")
        
        try:
            # step 2: fetch vacancies from hh.ru
            print(f"[Step 2] Fetching vacancies for '{position_query}' from hh.ru...")
            vacancies_data = self.hh_client.fetch_vacancies(position_query)
            print(f"[Step 2] Received {vacancies_data.get('found', 0)} vacancies")
            
            # step 3: deterministic skill extraction from vacancy texts
            print(f"[Step 3] Extracting skills from vacancy texts (deterministic)...")
            extracted_skills = extract_skills_from_vacancies(vacancies_data, top_n=25)
            position_name = get_position_name(vacancies_data, position_query)
            print(f"[Step 3] Identified position: '{position_name}'")
            print(f"[Step 3] Extracted {len(extracted_skills)} skills")

            if not extracted_skills:
                raise RuntimeError("No skills found in vacancies. Try a more specific query.")

            # step 4: save position (find or create)
            print(f"[Step 4] Saving position '{position_name}'...")
            position, position_created = self.position_repo.find_or_create(position_name)
            print(f"[Step 4] Position {'created' if position_created else 'already existed'} with id={position.id}")

            # step 5: save skills and SkillsPosition links
            print(f"[Step 5] Saving skills and links...")
            saved_skills = []

            for skill_data in extracted_skills:
                skill_name = skill_data.get('name')
                frequency = skill_data.get('frequency', 0)
                importance = skill_data.get('importance', 'not_important')
                
                # validate frequency range
                if frequency < 0 or frequency > 100:
                    print(f"  Warning: frequency {frequency} out of range, adjusting to 0-100")
                    frequency = max(0, min(100, frequency))
                
                # validate importance value
                if importance not in ['important', 'not_important']:
                    print(f"  Warning: importance '{importance}' invalid, setting to 'not_important'")
                    importance = 'not_important'
                
                # find or create skill
                skill, skill_created = self.skill_repo.find_or_create(skill_name)
                print(f"  - Skill '{skill_name}': {'created' if skill_created else 'existing'} (id={skill.id})")
                
                # create SkillsPosition link
                skills_position_record = SkillsPosition(
                    session_id=session_id,
                    position_id=position.id,
                    skill_id=skill.id,
                    frequency=frequency,
                    importance=importance,
                    analysis_date=datetime.now()
                )
                
                # save to database (will check for duplicates automatically)
                try:
                    saved_record = self.skills_position_repo.create(skills_position_record)
                    saved_skills.append({
                        "skill_id": skill.id,
                        "skill_name": skill_name,
                        "frequency": frequency,
                        "importance": importance
                    })
                    print(f"     Saved link (frequency={frequency}, importance={importance})")
                except ValueError as e:
                    # duplicate record - this is fine, just skip
                    print(f"     Link already exists: {e}")
            
            # step 6: return result to user
            print(f"\n[Step 6] Analysis complete!")
            print(f"  Total skills saved: {len(saved_skills)}")

            total_vacancies = vacancies_data.get('found', len(vacancies_data.get('items', [])))

            # update session with result
            created_session.ai_result = {
                "position_name": position_name,
                "skills_count": len(saved_skills),
                "total_vacancies": total_vacancies
            }
            self.session_repo.update(created_session)

            return saved_skills, total_vacancies
            
        except Exception as e:
            # if anything fails, we still have the session record for tracking
            print(f"\n[ERROR] Analysis failed: {e}")
            # update session with error info
            try:
                created_session.ai_result = {
                    "error": str(e),
                    "status": "failed"
                }
                self.session_repo.update(created_session)
            except:
                pass
            raise
    
    def get_user_position_history(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all position analysis sessions for a user
        
        Args:
            user_id (int): user id
        
        Returns:
            list[dict]: list of sessions with basic info
        """
        sessions = self.session_repo.find_by_user_and_branch(user_id, branch_type=1)
        
        result = []
        for session_record in sessions:
            result.append({
                "session_id": session_record.id,
                "search_query": session_record.search_query,
                "request_time": session_record.request_time,
                "ai_result": session_record.ai_result
            })
        
        return result
    
    def get_session_details(self, session_id: int) -> Dict[str, Any]:
        """
        Get detailed analysis results for a specific session
        
        Args:
            session_id (int): session id
        
        Returns:
            dict: session details with position and skills
        """
        session_record = self.session_repo.find_by_id(session_id)
        if not session_record:
            raise ValueError(f"Session with id {session_id} not found")
        
        # get all SkillsPosition records for this session
        skills_records = self.skills_position_repo.find_by_session(session_id)
        
        # get position info (from first record, all have same position_id per session)
        position = None
        skills = []
        
        for record in skills_records:
            if position is None and record.position_id:
                position_obj = self.position_repo.find_by_id(record.position_id)
                if position_obj:
                    position = {
                        "position_id": position_obj.id,
                        "position_name": position_obj.name
                    }
            
            skill_obj = self.skill_repo.find_by_id(record.skill_id)
            skills.append({
                "skill_id": record.skill_id,
                "skill_name": skill_obj.name if skill_obj else "Unknown",
                "frequency": record.frequency,
                "importance": record.importance,
                "analysis_date": record.analysis_date
            })
        
        return {
            "session_id": session_record.id,
            "search_query": session_record.search_query,
            "request_time": session_record.request_time,
            "position": position,
            "skills": skills,
            "ai_result": session_record.ai_result
        }