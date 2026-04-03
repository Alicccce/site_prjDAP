# repositories/base_repo.py
from sqlalchemy.orm import sessionmaker
from DataBase import engine

class BaseRepository:
    """A basic repository with common methods for working with a session"""
    
    def __init__(self):
        """Creates a session factory during initialization"""
        self.Session = sessionmaker(bind=engine)
    
    def get_session(self):
        """Returns a new session for working with the database"""
        return self.Session()
    
    def add_and_commit(self, session, entity):
        """Adds an entity to the session and commits"""
        try:
            session.add(entity)
            session.commit()
            return entity
        except Exception as e:
            session.rollback()
            raise e
    
    def delete_and_commit(self, session, entity):
        """Deletes the entity and commits"""
        try:
            session.delete(entity)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
