# -*- coding: utf-8 -*-
# tests/test_skills_position_advanced.py
import colorama
from colorama import init, Fore, Style
init(autoreset=True)

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from sqlalchemy import create_engine
from DataBase import Base, User, Skill, Session as DBSession, Position, SkillsPosition
from repositories.skills_position_repo import SkillsPositionRepository
from repositories.user_repo import UserRepository
from repositories.position_repo import PositionRepository
from repositories.skill_repo import SkillRepository
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
    """create test user, session, position and skills"""
    user_repo = UserRepository()
    position_repo = PositionRepository()
    skill_repo = SkillRepository()
    
    # create test user with unique email
    import time
    unique_email = f"test_advanced_{int(time.time()*1000)}@example.com"
    
    test_user = User(
        email=unique_email,
        name="Advanced Test User",
        password_hash="test_hash_123"
    )
    created_user = user_repo.create(test_user)
    
    # create test session
    base_repo = BaseRepository()
    session_db = base_repo.get_session()
    
    try:
        test_session = DBSession(
            user_id=created_user.id,
            branch_type=1,
            search_query="Advanced Test Query"
        )
        session_db.add(test_session)
        session_db.commit()
        session_db.refresh(test_session)
        test_session_id = test_session.id
    finally:
        session_db.close()
    
    # create test position
    position, _ = position_repo.find_or_create("Advanced Test Position")
    
    # create test skills
    skills = []
    skill_names = ["Python", "SQL", "Machine Learning", "Docker", "Git"]
    for name in skill_names:
        skill, _ = skill_repo.find_or_create(name)
        skills.append(skill)
    
    return created_user, test_session_id, position, skills


class TestSkillsPositionAdvanced:
    """Test suite for advanced SkillsPositionRepository methods"""
    
    def setup_method(self):
        """setup before each test"""
        self.test_engine, self.original_engine = setup_test_db()
        self.test_user, self.test_session_id, self.test_position, self.test_skills = create_test_data()
        self.repo = SkillsPositionRepository()
    
    def teardown_method(self):
        """cleanup after each test"""
        cleanup_test_db(self.original_engine)
    
    def test_create_batch_success(self):
        """test 1: batch create multiple records"""
        
        records = []
        for i, skill in enumerate(self.test_skills):
            record = SkillsPosition(
                session_id=self.test_session_id,
                position_id=self.test_position.id,
                skill_id=skill.id,
                frequency=90 - i * 5,
                importance="important" if i < 3 else "not_important",
                analysis_date=datetime.now()
            )
            records.append(record)
        
        # batch create
        created = self.repo.create_batch(records)
        
        assert len(created) == 5
        
        # verify all were saved by querying
        session_records = self.repo.find_by_session(self.test_session_id)
        assert len(session_records) == 5
        
        print("? test_create_batch_success passed")
    
    def test_create_batch_duplicate_fails(self):
        """test 2: batch create with duplicate should fail"""
        
        skill = self.test_skills[0]
        
        record = SkillsPosition(
            session_id=self.test_session_id,
            position_id=self.test_position.id,
            skill_id=skill.id,
            frequency=90,
            importance="important"
        )
        
        # create first record using regular create
        self.repo.create(record)
        
        # try to create duplicate in batch
        duplicate = SkillsPosition(
            session_id=self.test_session_id,
            position_id=self.test_position.id,
            skill_id=skill.id,
            frequency=95,
            importance="important"
        )
        
        try:
            self.repo.create_batch([duplicate])
            assert False, "Should raise ValueError for duplicate"
        except ValueError as e:
            assert "Duplicate" in str(e) or "already exists" in str(e)
        
        print("? test_create_batch_duplicate_fails passed")
    
    def test_create_or_update_new(self):
        """test 3: create_or_update should create new record"""
        
        skill = self.test_skills[0]
        
        record = SkillsPosition(
            session_id=self.test_session_id,
            position_id=self.test_position.id,
            skill_id=skill.id,
            frequency=85,
            importance="important"
        )
        
        created, is_new = self.repo.create_or_update(record)
        
        assert is_new is True
        assert created.record_id is not None
        assert created.frequency == 85
        
        print("? test_create_or_update_new passed")
    
    def test_create_or_update_existing(self):
        """test 4: create_or_update should update existing record"""
        
        skill = self.test_skills[0]
        
        # create initial record
        record = SkillsPosition(
            session_id=self.test_session_id,
            position_id=self.test_position.id,
            skill_id=skill.id,
            frequency=85,
            importance="important"
        )
        created, _ = self.repo.create_or_update(record)
        original_id = created.record_id
        
        # update with new values
        record2 = SkillsPosition(
            session_id=self.test_session_id,
            position_id=self.test_position.id,
            skill_id=skill.id,
            frequency=95,
            importance="not_important"
        )
        updated, is_new = self.repo.create_or_update(record2)
        
        assert is_new is False
        assert updated.record_id == original_id
        assert updated.frequency == 95
        assert updated.importance == "not_important"
        
        print("? test_create_or_update_existing passed")
    
    def test_find_by_session_with_details(self):
        """test 5: find_by_session_with_details returns names via JOIN"""
        
        # create test records
        for skill in self.test_skills[:3]:
            record = SkillsPosition(
                session_id=self.test_session_id,
                position_id=self.test_position.id,
                skill_id=skill.id,
                frequency=80,
                importance="important"
            )
            self.repo.create(record)
        
        # get with details
        details = self.repo.find_by_session_with_details(self.test_session_id)
        
        assert len(details) == 3
        assert "position_name" in details[0]
        assert "skill_name" in details[0]
        assert details[0]["position_name"] == "Advanced Test Position"
        
        # check skill names
        skill_names = [d["skill_name"] for d in details]
        assert "Python" in skill_names
        assert "SQL" in skill_names
        
        print("? test_find_by_session_with_details passed")
    
    def test_count_by_session(self):
        """test 6: count_by_session returns correct count"""
        
        # initially 0
        count = self.repo.count_by_session(self.test_session_id)
        assert count == 0
        
        # add 3 records
        for skill in self.test_skills[:3]:
            record = SkillsPosition(
                session_id=self.test_session_id,
                position_id=self.test_position.id,
                skill_id=skill.id,
                frequency=80,
                importance="important"
            )
            self.repo.create(record)
        
        count = self.repo.count_by_session(self.test_session_id)
        assert count == 3
        
        print("? test_count_by_session passed")
    
    def test_get_importance_stats(self):
        """test 7: get_importance_stats returns correct statistics"""
        
        # create records with mixed importance
        for i, skill in enumerate(self.test_skills[:5]):
            importance = "important" if i < 3 else "not_important"
            record = SkillsPosition(
                session_id=self.test_session_id,
                position_id=self.test_position.id,
                skill_id=skill.id,
                frequency=80,
                importance=importance
            )
            self.repo.create(record)
        
        stats = self.repo.get_importance_stats(self.test_session_id)
        
        assert stats["important"] == 3
        assert stats["not_important"] == 2
        assert stats["total"] == 5
        
        print("? test_get_importance_stats passed")
    
    def test_find_by_position_with_frequency(self):
        """test 8: find_by_position_with_frequency returns sorted skills"""
        
        # create records with different frequencies
        frequencies = [95, 85, 75, 90, 80]
        for i, skill in enumerate(self.test_skills):
            record = SkillsPosition(
                session_id=self.test_session_id,
                position_id=self.test_position.id,
                skill_id=skill.id,
                frequency=frequencies[i],
                importance="important"
            )
            self.repo.create(record)
        
        # get with frequency (should be sorted desc)
        skills = self.repo.find_by_position_with_frequency(self.test_position.id)
        
        # check sorting
        freqs = [s["frequency"] for s in skills]
        assert freqs == sorted(freqs, reverse=True)
        assert freqs[0] == 95
        
        print("? test_find_by_position_with_frequency passed")
    
    def test_delete_by_session(self):
        """test 9: delete_by_session removes all records for a session"""
        
        # create 3 records
        for skill in self.test_skills[:3]:
            record = SkillsPosition(
                session_id=self.test_session_id,
                position_id=self.test_position.id,
                skill_id=skill.id,
                frequency=80,
                importance="important"
            )
            self.repo.create(record)
        
        # verify they exist
        assert self.repo.count_by_session(self.test_session_id) == 3
        
        # delete all
        deleted = self.repo.delete_by_session(self.test_session_id)
        
        assert deleted == 3
        assert self.repo.count_by_session(self.test_session_id) == 0
        
        print("? test_delete_by_session passed")
    
    def test_find_by_session_with_details_empty(self):
        """test 10: find_by_session_with_details returns empty list for no data"""
        
        details = self.repo.find_by_session_with_details(99999)
        
        assert details == []
        
        print("? test_find_by_session_with_details_empty passed")


if __name__ == "__main__":
    print("Run with: pytest tests/test_skills_position_advanced.py -v")