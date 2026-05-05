# -*- coding: utf-8 -*-
# services/vacancy_analysis_service.py

import json
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

    def __init__(self):
        self.session_repo = SessionRepository()
        self.position_repo = PositionRepository()
        self.skill_repo = SkillRepository()
        self.skills_position_repo = SkillsPositionRepository()
        self.hh_client = HHClient()

    def analyzeByPosition(self, user_id: int, position_query: str):
        if not position_query or not position_query.strip():
            raise ValueError("Position query cannot be empty")

        # step 1: create search session
        print(f"[Step 1] Creating session for user {user_id}...")
        session_record = DBSession(
            user_id=user_id,
            branch_type=1,
            search_query=position_query,
            request_time=datetime.now()
        )
        created_session = self.session_repo.create(session_record)
        session_id = created_session.id
        print(f"[Step 1] Session created with id={session_id}")

        try:
            # step 2: fetch vacancies
            print(f"[Step 2] Fetching vacancies for '{position_query}'...")
            vacancies_data = self.hh_client.fetch_vacancies(position_query)
            print(f"[Step 2] Received {vacancies_data.get('found', 0)} vacancies")

            # step 3: extract skills
            print(f"[Step 3] Extracting skills...")
            extracted_skills = extract_skills_from_vacancies(vacancies_data, top_n=25)
            position_name = get_position_name(vacancies_data, position_query)
            print(f"[Step 3] Position: '{position_name}', skills: {len(extracted_skills)}")

            if not extracted_skills:
                raise RuntimeError("No skills found in vacancies. Try a more specific query.")

            # step 4: save position
            position, position_created = self.position_repo.find_or_create(position_name)
            print(f"[Step 4] Position id={position.id} ({'new' if position_created else 'existing'})")

            # step 5: save skills
            saved_skills = []
            for skill_data in extracted_skills:
                skill_name = skill_data.get('name')
                frequency = max(0, min(100, skill_data.get('frequency', 0)))
                importance = skill_data.get('importance', 'not_important')
                if importance not in ['important', 'not_important']:
                    importance = 'not_important'

                skill, _ = self.skill_repo.find_or_create(skill_name)

                sp_record = SkillsPosition(
                    session_id=session_id,
                    position_id=position.id,
                    skill_id=skill.id,
                    frequency=frequency,
                    importance=importance,
                    analysis_date=datetime.now()
                )
                try:
                    self.skills_position_repo.create(sp_record)
                    saved_skills.append({
                        "skill_id": skill.id,
                        "skill_name": skill_name,
                        "frequency": frequency,
                        "importance": importance
                    })
                except ValueError:
                    pass  # duplicate, skip

            total_vacancies = vacancies_data.get('found', len(vacancies_data.get('items', [])))
            print(f"[Step 6] Done. Skills saved: {len(saved_skills)}")

            # save result as JSON string (SQLite does not support dict)
            created_session.ai_result = json.dumps({
                "position_name": position_name,
                "skills_count": len(saved_skills),
                "total_vacancies": total_vacancies
            }, ensure_ascii=False)
            self.session_repo.update(created_session)

            return saved_skills, total_vacancies

        except Exception as e:
            print(f"[ERROR] Analysis failed: {e}")
            try:
                created_session.ai_result = json.dumps(
                    {"error": str(e), "status": "failed"},
                    ensure_ascii=False
                )
                self.session_repo.update(created_session)
            except Exception:
                pass
            raise

    def get_user_position_history(self, user_id: int) -> List[Dict[str, Any]]:
        sessions = self.session_repo.find_by_user_and_branch(user_id, branch_type=1)
        return [
            {
                "session_id": s.id,
                "search_query": s.search_query,
                "request_time": s.request_time,
                "ai_result": s.ai_result
            }
            for s in sessions
        ]

    def get_session_details(self, session_id: int) -> Dict[str, Any]:
        session_record = self.session_repo.find_by_id(session_id)
        if not session_record:
            raise ValueError(f"Session with id {session_id} not found")

        skills_records = self.skills_position_repo.find_by_session(session_id)
        position = None
        skills = []

        for record in skills_records:
            if position is None and record.position_id:
                pos_obj = self.position_repo.find_by_id(record.position_id)
                if pos_obj:
                    position = {"position_id": pos_obj.id, "position_name": pos_obj.name}

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
