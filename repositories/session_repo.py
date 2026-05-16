# -*- coding: utf-8 -*-
# repositories/session_repo.py
import colorama
from colorama import init, Fore, Style
init(autoreset=True)
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from repositories.base_repo import BaseRepository
from DataBase import Session as DBSession, User

class SessionRepository(BaseRepository):
    """
    Repository for user search sessions (table 'session')
    """
    
    def create(self, session_record):
        """
        Save a new search session
        
        Args:
            session_record (DBSession): Session object to save
        
        Returns:
            DBSession: saved session with id assigned
        
        Raises:
            ValueError: if user_id does not exist
        """
        session = self.get_session()
        try:
            # check if user exists
            if not self._user_exists(session, session_record.user_id):
                raise ValueError(f"User with id '{session_record.user_id}' does not exist")
            
            # set request_time if not provided
            if not session_record.request_time:
                session_record.request_time = datetime.now()
            
            session.add(session_record)
            session.commit()
            session.refresh(session_record)
            session.expunge(session_record)
            return session_record
            
        except IntegrityError as e:
            session.rollback()
            raise ValueError(f"Database integrity error: {e}")
        finally:
            session.close()
    
    def find_by_id(self, session_id):
        """
        Find session by id
        
        Args:
            session_id (int): session id
        
        Returns:
            DBSession or None: found session
        """
        session = self.get_session()
        try:
            record = session.query(DBSession).filter(
                DBSession.id == session_id
            ).first()
            
            if record:
                session.expunge(record)
            return record
        finally:
            session.close()
    
    def find_by_user(self, user_id):
        """
        Find all sessions for a specific user
        
        Args:
            user_id (int): user id
        
        Returns:
            list[DBSession]: list of sessions (may be empty)
        """
        session = self.get_session()
        try:
            records = session.query(DBSession).filter(
                DBSession.user_id == user_id
            ).order_by(DBSession.request_time.desc()).all()
            
            for record in records:
                session.expunge(record)
            return records
        finally:
            session.close()
    
    def find_by_user_and_branch(self, user_id, branch_type):
        """
        Find all sessions for a user by branch type
        
        Args:
            user_id (int): user id
            branch_type (int): 1 for position, 2 for skill
        
        Returns:
            list[DBSession]: list of sessions
        """
        session = self.get_session()
        try:
            records = session.query(DBSession).filter(
                DBSession.user_id == user_id,
                DBSession.branch_type == branch_type
            ).order_by(DBSession.request_time.desc()).all()
            
            for record in records:
                session.expunge(record)
            return records
        finally:
            session.close()
    
    def update(self, session_record):
        """
        Update session (e.g., add ai_result)
        
        Args:
            session_record (DBSession): session object with updated data
        
        Returns:
            DBSession: updated session
        """
        session = self.get_session()
        try:
            existing = self.find_by_id(session_record.id)
            if not existing:
                raise ValueError(f"Session with id '{session_record.id}' not found")
            
            merged = session.merge(session_record)
            session.commit()
            session.refresh(merged)
            session.expunge(merged)
            return merged
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def delete(self, session_id):
        """
        Delete session by id
        
        Args:
            session_id (int): session id
        
        Returns:
            bool: True if deleted
        """
        session = self.get_session()
        try:
            record = self.find_by_id(session_id)
            if not record:
                raise ValueError(f"Session with id '{session_id}' not found")
            
            to_delete = session.query(DBSession).filter(
                DBSession.id == session_id
            ).first()
            
            session.delete(to_delete)
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    # ��������������� ������
    
    def _user_exists(self, session, user_id):
        """check if user exists"""
        return session.query(User).filter(User.id == user_id).first() is not None
