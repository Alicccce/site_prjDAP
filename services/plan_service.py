# -*- coding: utf-8 -*-
# services/plan_service.py

from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from DataBase import Plan, PlanStep
from repositories.plan_repo import PlanRepository
from repositories.session_repo import SessionRepository
from repositories.skill_repo import SkillRepository
from repositories.skills_user_repo import SkillsUserRepository
from repositories.skills_position_repo import SkillsPositionRepository
from repositories.user_repo import UserRepository
from services.ai_assistant import AIAssistant


# Белый список ресурсов для обучающих материалов
ALLOWED_RESOURCES = [
    "stepik.org", "coursera.org", "youtube.com", "youtu.be",
    "habr.com", "leetcode.com", "codewars.com", "kaggle.com",
    "w3schools.com", "developer.mozilla.org", "learn.microsoft.com",
    "openedu.ru", "openedx.ru", "foxminded.ua", "prometheus.org.ua",
    "geeksforgeeks.org", "realpython.com", "python.org",
    "docs.python.org", "fastapi.tiangolo.com", "django-project.com",
    "ru.hexlet.io", "netology.ru", "skillbox.ru", "yandex.ru/learn",
    "practicum.yandex.ru", "udemy.com", "edx.org"
]


class PlanService:
    """
    Service for generating and managing personalized learning plans
    """

    def __init__(self):
        self.plan_repo = PlanRepository()
        self.session_repo = SessionRepository()
        self.skill_repo = SkillRepository()
        self.skills_user_repo = SkillsUserRepository()
        self.skills_position_repo = SkillsPositionRepository()
        self.user_repo = UserRepository()
        self.ai_assistant = AIAssistant()

    def generate_plan(self, user_id: int, session_id: int,
                      level: str = "middle", period: str = "6 месяцев",
                      time_per_day: str = "60") -> Dict[str, Any]:
        """
        Generate a personalized learning plan based on user's skill deficits.

        Steps:
        1. Get user's selected skills for the session (what they DON'T know)
        2. Get position skills for the session (what the market requires)
        3. Identify deficit skills
        4. Ask AI to generate a learning plan
        5. Save plan and steps to DB
        6. Return the plan
        """
        # step 1: validate session
        session_record = self.session_repo.find_by_id(session_id)
        if not session_record:
            raise ValueError(f"Session with id {session_id} not found")
        if session_record.user_id != user_id:
            raise ValueError(f"Session {session_id} does not belong to user {user_id}")

        # step 2: get user's selected skills (skills they marked as "don't know")
        user_skills = self.skills_user_repo.find_by_user_and_session_with_details(
            user_id, session_id
        )
        user_skill_ids = [s['skill_id'] for s in user_skills]
        user_skill_names = [s['skill_name'] for s in user_skills]

        # step 3: get position skills for this session
        position_skills = self.skills_position_repo.find_by_session(session_id)
        position_skill_names = []
        for ps in position_skills:
            skill_obj = self.skill_repo.find_by_id(ps.skill_id)
            if skill_obj:
                position_skill_names.append({
                    "name": skill_obj.name,
                    "frequency": ps.frequency,
                    "importance": ps.importance
                })

        # step 4: identify deficits (user doesn't know but market requires)
        deficit_skills = []
        for ps in position_skills:
            if ps.skill_id not in user_skill_ids:
                skill_obj = self.skill_repo.find_by_id(ps.skill_id)
                if skill_obj:
                    deficit_skills.append({
                        "name": skill_obj.name,
                        "frequency": ps.frequency,
                        "importance": ps.importance
                    })

        if not deficit_skills:
            # If no deficits found from DB, use user_skill_names as deficits
            deficit_skills = [{"name": name, "frequency": 50, "importance": "important"}
                              for name in user_skill_names]

        # step 5: ask AI to generate learning plan
        plan_data = self.ai_assistant.generateLearningPlan(
            deficit_skills=deficit_skills,
            level=level,
            period=period,
            time_per_day=time_per_day
        )

        # step 6: calculate ending_date based on period
        period_months = self._parse_period_months(period)
        ending_date = date.today() + timedelta(days=period_months * 30)

        # step 7: create Plan record
        plan_title = plan_data.get("title", f"План обучения: {session_record.search_query}")

        plan = Plan(
            user_id=user_id,
            session_id=session_id,
            title=plan_title,
            created_date=date.today(),
            ending_date=ending_date,
            efficiency=None
        )
        saved_plan = self.plan_repo.create_plan(plan)

        # step 8: create PlanStep records
        steps = plan_data.get("steps", [])
        plan_steps = []
        for i, step_data in enumerate(steps, start=1):
            skill_name = step_data.get("skill", "General")
            skill, _ = self.skill_repo.find_or_create(skill_name)

            # Filter materials to only allow whitelisted resources
            materials = step_data.get("materials", [])
            safe_materials = self._filter_materials(materials)

            plan_step = PlanStep(
                plan_id=saved_plan.id,
                skill_id=skill.id,
                step_number=i,
                description=step_data.get("description", ""),
                material=safe_materials
            )
            plan_steps.append(plan_step)

        if plan_steps:
            self.plan_repo.create_steps_bulk(plan_steps)

        # step 9: return full plan
        return self.plan_repo.get_full_plan(saved_plan.id)

    def get_user_plans(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all plans for a user"""
        plans = self.plan_repo.find_plans_by_user(user_id)
        result = []
        for plan in plans:
            result.append({
                "id": plan.id,
                "title": plan.title,
                "created_date": str(plan.created_date),
                "ending_date": str(plan.ending_date),
                "efficiency": plan.efficiency,
                "session_id": plan.session_id
            })
        return result

    def get_plan(self, plan_id: int) -> Optional[Dict[str, Any]]:
        """Get full plan with steps"""
        return self.plan_repo.get_full_plan(plan_id)

    def update_plan(self, plan_id: int, title: str = None,
                    ending_date: str = None, efficiency: int = None) -> Dict[str, Any]:
        """Update plan metadata"""
        plan = self.plan_repo.find_plan_by_id(plan_id)
        if not plan:
            raise ValueError(f"Plan with id {plan_id} not found")

        if title is not None:
            plan.title = title
        if ending_date is not None:
            plan.ending_date = date.fromisoformat(ending_date)
        if efficiency is not None:
            plan.efficiency = efficiency

        self.plan_repo.update_plan(plan)
        return self.plan_repo.get_full_plan(plan_id)

    def update_step(self, step_id: int, description: str = None,
                    material=None) -> Dict[str, Any]:
        """Update a plan step"""
        step = self.plan_repo.find_step_by_id(step_id)
        if not step:
            raise ValueError(f"PlanStep with id {step_id} not found")

        if description is not None:
            step.description = description
        if material is not None:
            step.material = material

        self.plan_repo.update_step(step)

        updated_step = self.plan_repo.find_step_by_id(step_id)
        return {
            "id": updated_step.id,
            "plan_id": updated_step.plan_id,
            "skill_id": updated_step.skill_id,
            "step_number": updated_step.step_number,
            "description": updated_step.description,
            "material": updated_step.material
        }

    def delete_plan(self, plan_id: int) -> bool:
        """Delete a plan"""
        return self.plan_repo.delete_plan(plan_id)

    def _parse_period_months(self, period: str) -> int:
        """Parse period string to months"""
        period_lower = period.lower()
        if "месяц" in period_lower:
            try:
                num = int(''.join(c for c in period_lower if c.isdigit()))
                return num
            except ValueError:
                return 6
        elif "недел" in period_lower:
            try:
                num = int(''.join(c for c in period_lower if c.isdigit()))
                return max(1, num // 4)
            except ValueError:
                return 2
        elif "год" in period_lower:
            return 12
        return 6

    def _filter_materials(self, materials: list) -> list:
        """Filter materials to only include whitelisted resources"""
        if not materials:
            return []

        safe = []
        for mat in materials:
            url = mat.get("url", "") if isinstance(mat, dict) else str(mat)
            if any(domain in url.lower() for domain in ALLOWED_RESOURCES):
                safe.append(mat)
            else:
                # Mark as unverified instead of removing
                if isinstance(mat, dict):
                    mat["verified"] = False
                    safe.append(mat)
                else:
                    safe.append({"url": url, "verified": False})
        return safe
