# -*- coding: utf-8 -*-
# tests/test_user.py
import sys
import os
import time
import pytest


# Add the path to the Project root folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from DataBase import Base, User
from repositories.user_repo import UserRepository
from sqlalchemy import create_engine
import tempfile

def test_user_repository():
    """Testing UserRepository with a temporary database"""
    # Saving the original engine
    from DataBase import engine as original_engine
    import DataBase as db_module
    
    # Creating a temporary database for tests
    test_engine = create_engine('sqlite:///:memory:', echo=False)
    
    # Creating tables in the test database
    Base.metadata.create_all(test_engine)
    email=f"test_{int(time.time()*1000)}@example.com",
    # Temporarily replacing the engine
    db_module.engine = test_engine
    
    try:
        repo = UserRepository()
        
        # Test 1: Creating a User
        print("Test 1: Creating a User")
        unique_email = f"test_{int(time.time()*1000)}@example.com"
        new_user = User(
            email=unique_email,
            name="Test User",
            password_hash="hashed_password_123"
        )
        created = repo.create(new_user)
        assert created.id is not None
        assert created.email == unique_email
        print(f"The user was created with the id ={created.id}")
        
        # Test 2: Email Search
        print("\nTest 2: Search by email")
        found = repo.find_by_email(unique_email)
        assert found is not None
        assert found.name == "Test User"
        print(f"The user has been found: {found.name}")
        
        # Test 3: Attempt to create a duplicate email
        print("\nTest 3: Duplicate Protection")
        duplicate_user = User(
            email=unique_email,
            name="Another User",
            password_hash="another_hash"
        )
        try:
            repo.create(duplicate_user)
            print("Error: a duplicate was created")
        except ValueError as e:
            print(f"The error has been intercepted: {e}")
        
        # Test 4: User Update
        print("\nTest 4: Data Update")
        created.name = "Updated Name"
        updated = repo.update(created)
        assert updated.name == "Updated Name"
        print(f"Name has been updated to: {updated.name}")
        
        # Test 5: Deleting a User
        print("\nTest 5: Deleting a User")
        result = repo.delete(created.id)
        assert result is True
        deleted_check = repo.find_by_id(created.id)
        assert deleted_check is None
        print("The user has been deleted")
        
        print("\nAll tests passed successfully")
        
    finally:
        # Restoring the original engine
        db_module.engine = original_engine

if __name__ == "__main__":
    test_user_repository()
