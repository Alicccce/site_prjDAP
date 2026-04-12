# -*- coding: utf-8 -*-
# tests/test_skills_position.py
import colorama
from colorama import init, Fore, Style
# Инициализация colorama (автоматически настраивает кодировку)
init(autoreset=True)
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from sqlalchemy import create_engine
from DataBase import Base, User, Skill, Session as DBSession, Position, SkillsPosition
from repositories.skills_position_repo import SkillsPositionRepository
from repositories.user_repo import UserRepository
from repositories.base_repo import BaseRepository

def setup_test_db():
    """create temporary in-memory database for tests"""
    test_engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(test_engine)
    
    import DataBase as db_module
    original_engine = db_module.engine
    db_module.engine = test_engine
    
    return test_engine, original_engine

def cleanup_test_db(original_engine):
    """restore original engine"""
    import DataBase as db_module
    db_module.engine = original_engine

def create_test_data():
    """create test user, session, position and skill"""
    user_repo = UserRepository()
    
    # create test user
    test_user = User(
        email="test_position@example.com",
        name="Position Test User",
        password_hash="test_hash_123"
    )
    created_user = user_repo.create(test_user)
    
    # create test session (using a fresh session)
    base_repo = BaseRepository()
    session_db = base_repo.get_session()
    
    try:
        test_session = DBSession(
            user_id=created_user.id,
            branch_type=1,
            search_query="test query for positions"
        )
        session_db.add(test_session)
        session_db.commit()
        session_db.refresh(test_session)
        # save id before closing
        test_session_id = test_session.id
    finally:
        session_db.close()
    
    # create test position (using a fresh session)
    session_pos = base_repo.get_session()
    try:
        test_position = Position(name="Data Scientist")
        session_pos.add(test_position)
        session_pos.commit()
        session_pos.refresh(test_position)
        test_position_id = test_position.id
    finally:
        session_pos.close()
    
    # create test skill (using a fresh session)
    session_skill = base_repo.get_session()
    try:
        test_skill = Skill(name="Machine Learning")
        session_skill.add(test_skill)
        session_skill.commit()
        session_skill.refresh(test_skill)
        test_skill_id = test_skill.id
    finally:
        session_skill.close()
    
    # return objects with ids (but detached from session)
    return created_user, test_session_id, test_position_id, test_skill_id

def test_skills_position_repository():
    """test SkillsPositionRepository"""
    
    test_engine, original_engine = setup_test_db()
    
    try:
        # create test data (returns ids, not objects with session)
        test_user, test_session_id, test_position_id, test_skill_id = create_test_data()
        print(f"\nTest data created:")
        print(f"  - user_id={test_user.id}")
        print(f"  - session_id={test_session_id}")
        print(f"  - position_id={test_position_id}")
        print(f"  - skill_id={test_skill_id}")
        
        repo = SkillsPositionRepository()
        
        # test 1: create record (using ids, not objects)
        print("\nTest 1: create new record")
        new_record = SkillsPosition(
            session_id=test_session_id,
            position_id=test_position_id,
            skill_id=test_skill_id,
            frequency=85,
            importance="important",
            analysis_date=datetime.now()
        )
        created = repo.create(new_record)
        assert created.record_id is not None
        assert created.frequency == 85
        assert created.importance == "important"
        print(f"Record created with record_id={created.record_id}")
        
        # test 2: find by id
        print("\nTest 2: find by id")
        found = repo.find_by_id(created.record_id)
        assert found is not None
        assert found.position_id == test_position_id
        print(f"Record found by id")
        
        # test 3: find by session
        print("\nTest 3: find by session")
        session_records = repo.find_by_session(test_session_id)
        assert len(session_records) >= 1
        print(f"Found {len(session_records)} records for session")
        
        # test 4: find by position (returns dict with skill names)
        print("\nTest 4: find by position")
        position_skills = repo.find_by_position(test_position_id)
        assert len(position_skills) >= 1
        assert position_skills[0]["skill_name"] == "Machine Learning"
        assert position_skills[0]["frequency"] == 85
        print(f"Position requires: {[s['skill_name'] for s in position_skills]}")
        
        # test 5: find by skill (returns dict with position names)
        print("\nTest 5: find by skill ---")
        skill_positions = repo.find_by_skill(test_skill_id)
        assert len(skill_positions) >= 1
        assert skill_positions[0]["position_name"] == "Data Scientist"
        print(f"Skill appears in: {[p['position_name'] for p in skill_positions]}")
        
        # test 6: duplicate protection
        print("\nTest 6: duplicate protection")
        duplicate_record = SkillsPosition(
            session_id=test_session_id,
            position_id=test_position_id,
            skill_id=test_skill_id,
            frequency=90,
            importance="important"
        )
        try:
            repo.create(duplicate_record)
            print("Error: duplicate was created")
            assert False
        except ValueError as e:
            print(f"Duplicate correctly rejected: {str(e)[:60]}...")
        
        # test 7: update record (change frequency)
        print("\nTest 7: update record")
        created.frequency = 95
        updated = repo.update(created)
        assert updated.frequency == 95
        print(f"Frequency updated to {updated.frequency}")
        
        # test 8: get skill ids by position
        print("\nTest 8: get skill ids by position")
        skill_ids = repo.get_skill_ids_by_position(test_position_id)
        assert test_skill_id in skill_ids
        print(f"Position has skill ids: {skill_ids}")
        
        # test 9: get top skills for position
        print("\nTest 9: get top skills for position")
        top_skills = repo.get_top_skills_for_position(test_position_id, limit=5)
        assert len(top_skills) >= 1
        assert top_skills[0]["skill_name"] == "Machine Learning"
        print(f"Top skills: {[s['skill_name'] for s in top_skills]}")
        
        # test 10: find unique (should return existing record)
        print("\nTest 10: find unique")
        unique_check = repo.find_unique(
            test_session_id,
            test_position_id,
            test_skill_id
        )
        assert unique_check is not None
        assert unique_check.record_id == created.record_id
        print(f"Find_unique returned existing record")
        
        # test 11: delete record
        print("\nTest 11: delete record")
        result = repo.delete(created.record_id)
        assert result is True
        deleted_check = repo.find_by_id(created.record_id)
        assert deleted_check is None
        print(f"Record deleted")
        
        # test 12: verify deletion
        print("\nTest 12: verify deletion")
        session_records_after = repo.find_by_session(test_session_id)
        assert len(session_records_after) == 0
        print(f"No records left for session")
        
        print("ALL SKILLS_POSITION TESTS PASSED!")
        
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        cleanup_test_db(original_engine)

if __name__ == "__main__":
    test_skills_position_repository()