# -*- coding: utf-8 -*-
# repositories/plan_repo.py

from datetime import datetime, date
from typing import List, Dict, Any, Optional
from sqlalchemy.exc import IntegrityError
from repositories.base_repo import BaseRepository
from DataBase import Plan, PlanStep, Skill


class PlanRepository(BaseRepository):
    """Repository for working with Plan and PlanStep"""

    # ==================== Plan ====================

    def create_plan(self, plan: Plan) -> Plan:
        """Create a new learning plan"""
        session = self.get_session()
        try:
            session.add(plan)
            session.commit()
            session.refresh(plan)
            session.expunge(plan)
            return plan
        except IntegrityError as e:
            session.rollback()
            raise ValueError(f"Database integrity error: {e}")
        finally:
            session.close()

    def find_plan_by_id(self, plan_id: int) -> Optional[Plan]:
        """Find plan by id"""
        session = self.get_session()
        try:
            plan = session.query(Plan).filter(Plan.id == plan_id).first()
            if plan:
                session.expunge(plan)
            return plan
        finally:
            session.close()

    def find_plans_by_user(self, user_id: int) -> List[Plan]:
        """Find all plans for a user"""
        session = self.get_session()
        try:
            plans = session.query(Plan).filter(
                Plan.user_id == user_id
            ).order_by(Plan.created_date.desc()).all()
            for plan in plans:
                session.expunge(plan)
            return plans
        finally:
            session.close()

    def find_plans_by_user_and_session(self, user_id: int, session_id: int) -> List[Plan]:
        """Find plans for a user and session"""
        session = self.get_session()
        try:
            plans = session.query(Plan).filter(
                Plan.user_id == user_id,
                Plan.session_id == session_id
            ).order_by(Plan.created_date.desc()).all()
            for plan in plans:
                session.expunge(plan)
            return plans
        finally:
            session.close()

    def update_plan(self, plan: Plan) -> Plan:
        """Update plan"""
        session = self.get_session()
        try:
            merged = session.merge(plan)
            session.commit()
            session.refresh(merged)
            session.expunge(merged)
            return merged
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_plan(self, plan_id: int) -> bool:
        """Delete plan by id (cascades to steps)"""
        session = self.get_session()
        try:
            plan = session.query(Plan).filter(Plan.id == plan_id).first()
            if not plan:
                raise ValueError(f"Plan with id '{plan_id}' not found")
            session.delete(plan)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    # ==================== PlanStep ====================

    def create_step(self, step: PlanStep) -> PlanStep:
        """Create a new plan step"""
        session = self.get_session()
        try:
            session.add(step)
            session.commit()
            session.refresh(step)
            session.expunge(step)
            return step
        except IntegrityError as e:
            session.rollback()
            raise ValueError(f"Database integrity error: {e}")
        finally:
            session.close()

    def create_steps_bulk(self, steps: List[PlanStep]) -> List[PlanStep]:
        """Create multiple plan steps at once"""
        session = self.get_session()
        try:
            for step in steps:
                session.add(step)
            session.commit()
            for step in steps:
                session.refresh(step)
                session.expunge(step)
            return steps
        except IntegrityError as e:
            session.rollback()
            raise ValueError(f"Database integrity error: {e}")
        finally:
            session.close()

    def find_steps_by_plan(self, plan_id: int) -> List[Dict[str, Any]]:
        """Find all steps for a plan with skill names"""
        session = self.get_session()
        try:
            results = session.query(
                PlanStep.id,
                PlanStep.plan_id,
                PlanStep.skill_id,
                Skill.name.label("skill_name"),
                PlanStep.step_number,
                PlanStep.description,
                PlanStep.material
            ).join(
                Skill, PlanStep.skill_id == Skill.id
            ).filter(
                PlanStep.plan_id == plan_id
            ).order_by(
                PlanStep.step_number
            ).all()

            return [
                {
                    "id": r.id,
                    "plan_id": r.plan_id,
                    "skill_id": r.skill_id,
                    "skill_name": r.skill_name,
                    "step_number": r.step_number,
                    "description": r.description,
                    "material": r.material
                }
                for r in results
            ]
        finally:
            session.close()

    def find_step_by_id(self, step_id: int) -> Optional[PlanStep]:
        """Find step by id"""
        session = self.get_session()
        try:
            step = session.query(PlanStep).filter(PlanStep.id == step_id).first()
            if step:
                session.expunge(step)
            return step
        finally:
            session.close()

    def update_step(self, step: PlanStep) -> PlanStep:
        """Update plan step"""
        session = self.get_session()
        try:
            merged = session.merge(step)
            session.commit()
            session.refresh(merged)
            session.expunge(merged)
            return merged
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_step(self, step_id: int) -> bool:
        """Delete step by id"""
        session = self.get_session()
        try:
            step = session.query(PlanStep).filter(PlanStep.id == step_id).first()
            if not step:
                raise ValueError(f"PlanStep with id '{step_id}' not found")
            session.delete(step)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_steps_by_plan(self, plan_id: int) -> int:
        """Delete all steps for a plan"""
        session = self.get_session()
        try:
            deleted_count = session.query(PlanStep).filter(
                PlanStep.plan_id == plan_id
            ).delete()
            session.commit()
            return deleted_count
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    # ==================== Full Plan with Steps ====================

    def get_full_plan(self, plan_id: int) -> Optional[Dict[str, Any]]:
        """Get plan with all steps and skill names"""
        plan = self.find_plan_by_id(plan_id)
        if not plan:
            return None

        steps = self.find_steps_by_plan(plan_id)

        return {
            "id": plan.id,
            "user_id": plan.user_id,
            "session_id": plan.session_id,
            "title": plan.title,
            "created_date": str(plan.created_date),
            "ending_date": str(plan.ending_date),
            "efficiency": plan.efficiency,
            "steps": steps
        }
