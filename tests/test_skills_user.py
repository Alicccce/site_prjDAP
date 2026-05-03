# -*- coding: utf-8 -*-
# tests/test_skills_user.py
import colorama
from colorama import init, Fore, Style
init(autoreset=True)
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from DataBase import Base, User, Skill, Session as DBSession, SkillsUser
from repositories.skills_user_repo import SkillsUserRepository
from repositories.user_repo import UserRepository
from repositories.base_repo import BaseRepository

def setup_test_db():
    """create temporary in-memory database for tests"""
    test_engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(test_engine)
    
    # temporarily replace engine
    import DataBase as db_module
    original_engine = db_module.engine
    db_module.engine = test_engine
    
    return test_engine, original_engine

def cleanup_test_db(original_engine):
    """restore original engine"""
    import DataBase as db_module
    db_module.engine = original_engine

def create_test_data():
    """create test users, skills and sessions"""
    user_repo = UserRepository()
    
    # create test user
    test_user = User(
        email="test_skills_user@example.com",
        name="Skills Test User",
        password_hash="test_hash_123"
    )
    created_user = user_repo.create(test_user)
    
    # create test skill
    session = BaseRepository().get_session()
    test_skill = Skill(name="Python")
    session.add(test_skill)
    session.commit()
    session.refresh(test_skill)
    session.close()
    
    # create test session
    session2 = BaseRepository().get_session()
    test_session = DBSession(
        user_id=created_user.id,
        branch_type=1,
        search_query="test query"
    )
    session2.add(test_session)
    session2.commit()
    session2.refresh(test_session)
    session2.close()
    
    return created_user, test_skill, test_session

def cleanup_test_data(user_id):
    """clean up test data"""
    user_repo = UserRepository()
    try:
        user_repo.delete(user_id)
    except:
        pass

def test_skills_user_repository():
    """Test SkillsUserRepository"""
    
    test_engine, original_engine = setup_test_db()
    
    try:
        # create test data
        test_user, test_skill, test_session = create_test_data()
        print(f"\nTest data created: user_id={test_user.id}, skill_id={test_skill.id}, session_id={test_session.id}")
        
        repo = SkillsUserRepository()
        
        # test 1: create skills user record
        print("\nTest 1: create new record")
        new_record = SkillsUser(
            user_id=test_user.id,
            skill_id=test_skill.id,
            session_id=test_session.id,
            specified_date=datetime.now()
        )
        created = repo.create(new_record)
        assert created.record_id is not None
        print(f"Record created with record_id={created.record_id}")
        
        # test 2: find by id
        print("\nTest 2: find by id")
        found = repo.find_by_id(created.record_id)
        assert found is not None
        assert found.user_id == test_user.id
        print(f"Record found by id={found.record_id}")
        
        # test 3: find by user
        print("\nTest 3: find by user")
        user_records = repo.find_by_user(test_user.id)
        assert len(user_records) >= 1
        print(f"Found {len(user_records)} records for user")
        
        # test 4: find by user and session
        print("\nTest 4: find by user and session")
        skills_list = repo.find_by_user_and_session(test_user.id, test_session.id)
        assert len(skills_list) >= 1
        assert skills_list[0]["skill_name"] == "Python"
        print(f"Found skills: {[s['skill_name'] for s in skills_list]}")
        
        # test 5: duplicate protection
        print("\nTest 5: duplicate protection")
        duplicate_record = SkillsUser(
            user_id=test_user.id,
            skill_id=test_skill.id,
            session_id=test_session.id
        )
        try:
            repo.create(duplicate_record)
            print("Error: duplicate was created")
            assert False
        except ValueError as e:
            print(f"Duplicate correctly rejected: {str(e)[:50]}...")
        
        # test 6: update record
        print("\nTest 6: update record")
        new_date = datetime.now()
        created.specified_date = new_date
        updated = repo.update(created)
        assert updated.specified_date is not None
        print(f"Record updated")
        
        # test 7: get skill names by user
        print("\nTest 7: get skill names by user")
        skill_names = repo.get_skill_names_by_user(test_user.id)
        assert "Python" in skill_names
        print(f"User skills: {skill_names}")
        
        # test 8: delete record
        print("\nTest 8: delete record")
        result = repo.delete(created.record_id)
        assert result is True
        deleted_check = repo.find_by_id(created.record_id)
        assert deleted_check is None
        print(f"Record deleted")
        
        # test 9: find by user after deletion
        print("\nTest 9: verify deletion")
        user_records_after = repo.find_by_user(test_user.id)
        assert len(user_records_after) == 0
        print(f"No records left for user")
        
        print("ALL SKILLS_USER TESTS PASSED")
       
        
    except Exception as e:
        print(f"\nTest failed: {e}")
        raise
    finally:
        cleanup_test_db(original_engine)

if __name__ == "__main__":
    test_skills_user_repository()
