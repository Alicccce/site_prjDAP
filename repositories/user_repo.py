# repositories/user_repo.py
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from repositories.base_repo import BaseRepository
from DataBase import User

class UserRepository(BaseRepository):
    """Repository for working with users"""
    
    def create(self, user):
        """Save a new user to the database"""
        session = self.get_session()
        try:
            # Checking if there is a user with this email address
            existing_user = self.find_by_email(user.email)
            if existing_user:
                raise ValueError(f"User with email '{user.email}' already exists")
            
            if not user.registration_date:
                user.registration_date = datetime.now()
            
            session.add(user)
            session.commit()
            # We update the object so that it remains attached to the session
            session.refresh(user)
            return user
        except IntegrityError as e:
            session.rollback()
            raise ValueError(f"Database integrity error: {e}")
        finally:
            session.close()
    
    def find_by_id(self, user_id):
        """Find a user by ID"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                # Keep the object active in the session
                session.expunge(user)  # Disconnecting it so that it can be used outside of the session
            return user
        finally:
            session.close()
    
    def find_by_email(self, email):
        """Find a user by email (for logging in)"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.email == email).first()
            if user:
                session.expunge(user)  # Detaching
            return user
        finally:
            session.close()
    
    def update(self, user):
        """Update user data"""
        session = self.get_session()
        try:
            # Checking if a user exists
            existing_user = self.find_by_id(user.id)
            if not existing_user:
                raise ValueError(f"User with id '{user.id}' not found")
            
            # Attach the object to the session and update it
            merged_user = session.merge(user)
            session.commit()
            session.refresh(merged_user)
            session.expunge(merged_user)  # Disconnect before returning
            return merged_user
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def delete(self, user_id):
        """Delete a user by ID"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User with id '{user_id}' not found")
            
            session.delete(user)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()