# -*- coding: utf-8 -*-
# repositories/position_repo.py
import colorama
from colorama import init, Fore, Style
init(autoreset=True)
from sqlalchemy.exc import IntegrityError
from repositories.base_repo import BaseRepository
from DataBase import Position

class PositionRepository(BaseRepository):
    """
    Repository for positions (table 'position')
    Ensures unique position names (case-insensitive by logic)
    """
    
    def create(self, position):
        """
        Save a new position
        
        Args:
            position (Position): Position object to save
        
        Returns:
            Position: saved position with id assigned
        
        Raises:
            ValueError: if position with same name already exists
        """
        session = self.get_session()
        try:
            # check if position with same name exists
            existing = self.find_by_name(position.name)
            if existing:
                raise ValueError(f"Position with name '{position.name}' already exists")
            
            session.add(position)
            session.commit()
            session.refresh(position)
            session.expunge(position)
            return position
            
        except IntegrityError as e:
            session.rollback()
            raise ValueError(f"Database integrity error: {e}")
        finally:
            session.close()
    
    def find_by_id(self, position_id):
        """
        Find position by id
        
        Args:
            position_id (int): position id
        
        Returns:
            Position or None: found position
        """
        session = self.get_session()
        try:
            position = session.query(Position).filter(
                Position.id == position_id
            ).first()
            
            if position:
                session.expunge(position)
            return position
        finally:
            session.close()
    
    def find_by_name(self, name):
        """
        Find position by exact name (case-insensitive in search)
        
        Args:
            name (str): position name
        
        Returns:
            Position or None: found position
        """
        session = self.get_session()
        try:
            from sqlalchemy import func
            position = session.query(Position).filter(
                func.lower(Position.name) == func.lower(name)
            ).first()
            
            if position:
                session.expunge(position)
            return position
        finally:
            session.close()
    
    def find_all(self):
        """
        Get all positions (for admin panel)
        
        Returns:
            list[Position]: list of all positions
        """
        session = self.get_session()
        try:
            positions = session.query(Position).order_by(Position.name).all()
            
            for position in positions:
                session.expunge(position)
            return positions
        finally:
            session.close()
    
    def find_or_create(self, name):
        """
        IMPORTANT METHOD: Check if position exists, if not - create new
        
        Args:
            name (str): position name
        
        Returns:
            tuple (Position, bool): (position object, created flag)
            created flag is True if new record was created, False if existed
        """
        session = self.get_session()
        try:
            from sqlalchemy import func
            
            # try to find existing
            existing = session.query(Position).filter(
                func.lower(Position.name) == func.lower(name)
            ).first()
            
            if existing:
                session.expunge(existing)
                return existing, False
            
            # create new position
            new_position = Position(name=name)
            session.add(new_position)
            session.commit()
            session.refresh(new_position)
            session.expunge(new_position)
            return new_position, True
            
        except IntegrityError as e:
            session.rollback()
            # if duplicate was created by another process, try to find again
            existing = self.find_by_name(name)
            if existing:
                return existing, False
            raise ValueError(f"Failed to create position: {e}")
        finally:
            session.close()
    
    def update(self, position):
        """
        Update position name
        
        Args:
            position (Position): position object with updated data
        
        Returns:
            Position: updated position
        """
        session = self.get_session()
        try:
            existing = self.find_by_id(position.id)
            if not existing:
                raise ValueError(f"Position with id '{position.id}' not found")
            
            # check name uniqueness
            name_exists = session.query(Position).filter(
                Position.id != position.id,
                Position.name == position.name
            ).first()
            if name_exists:
                raise ValueError(f"Position with name '{position.name}' already exists")
            
            merged = session.merge(position)
            session.commit()
            session.refresh(merged)
            session.expunge(merged)
            return merged
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def delete(self, position_id):
        """
        Delete position by id
        
        Args:
            position_id (int): position id
        
        Returns:
            bool: True if deleted
        """
        session = self.get_session()
        try:
            position = self.find_by_id(position_id)
            if not position:
                raise ValueError(f"Position with id '{position_id}' not found")
            
            to_delete = session.query(Position).filter(
                Position.id == position_id
            ).first()
            
            session.delete(to_delete)
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
