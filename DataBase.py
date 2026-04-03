# -*- coding: utf-8 -*-
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date, Text, JSON, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

# Подключение к БД
engine = create_engine('sqlite:///database.db', echo=False)
Base = declarative_base()

# Объявление классов с индексами

# 1. Users
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    registration_date = Column(DateTime, nullable=False, default=datetime.now)
    
    # Индексы
    __table_args__ = (
        Index('idx_users_email', 'email'),
    )

# 2. Session
class Session(Base):
    __tablename__ = 'session'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    branch_type = Column(Integer, nullable=False)
    search_query = Column(Text)
    request_time = Column(DateTime, nullable=False, default=datetime.now)
    ai_result = Column(JSON)
    
    # Индексы и ограничения
    __table_args__ = (
        CheckConstraint('branch_type IN (1, 2)', name='check_branch_type'),
        Index('idx_session_user_id', 'user_id'),
        Index('idx_session_request_time', 'request_time'),
        Index('idx_session_branch_type', 'branch_type'),
    )

# 3. Position
class Position(Base):
    __tablename__ = 'position'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    
    __table_args__ = (
        Index('idx_position_name', 'name'),
    )

# 4. Skills
class Skill(Base):
    __tablename__ = 'skills'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    
    __table_args__ = (
        Index('idx_skills_name', 'name'),
    )

# 5. Skills_User
class SkillsUser(Base):
    __tablename__ = 'skills_user'
    
    record_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    skill_id = Column(Integer, ForeignKey('skills.id', ondelete='CASCADE'), nullable=False)
    session_id = Column(Integer, ForeignKey('session.id', ondelete='CASCADE'), nullable=False)
    specified_date = Column(DateTime, nullable=False, default=datetime.now)
    
    # Индексы
    __table_args__ = (
        Index('idx_skills_user_user_id', 'user_id'),
        Index('idx_skills_user_skill_id', 'skill_id'),
        Index('idx_skills_user_session_id', 'session_id'),
        Index('idx_skills_user_specified_date', 'specified_date'),
    )

# 6. Skills_Position
class SkillsPosition(Base):
    __tablename__ = 'skills_position'
    
    record_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('session.id', ondelete='CASCADE'), nullable=False)
    position_id = Column(Integer, ForeignKey('position.id', ondelete='CASCADE'), nullable=False)
    skill_id = Column(Integer, ForeignKey('skills.id', ondelete='CASCADE'), nullable=False)
    frequency = Column(Integer)
    importance = Column(String(50))
    analysis_date = Column(DateTime, nullable=False, default=datetime.now)
    
    # Индексы и ограничения
    __table_args__ = (
        CheckConstraint('frequency >= 0 AND frequency <= 100', name='check_frequency'),
        CheckConstraint("importance IN ('important', 'not_important')", name='check_importance'),
        Index('idx_skills_position_session_id', 'session_id'),
        Index('idx_skills_position_position_id', 'position_id'),
        Index('idx_skills_position_skill_id', 'skill_id'),
        Index('idx_skills_position_analysis_date', 'analysis_date'),
    )

# 7. Plan
class Plan(Base):
    __tablename__ = 'plan'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    session_id = Column(Integer, ForeignKey('session.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=False)
    created_date = Column(Date, nullable=False, default=datetime.now)
    ending_date = Column(Date, nullable=False)
    efficiency = Column(Integer)
    
    # Индексы и ограничения
    __table_args__ = (
        CheckConstraint('ending_date >= created_date', name='check_dates'),
        Index('idx_plan_user_id', 'user_id'),
        Index('idx_plan_session_id', 'session_id'),
        Index('idx_plan_created_date', 'created_date'),
        Index('idx_plan_ending_date', 'ending_date'),
    )

# 8. Plan_Steps
class PlanStep(Base):
    __tablename__ = 'plan_steps'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey('plan.id', ondelete='CASCADE'), nullable=False)
    skill_id = Column(Integer, ForeignKey('skills.id', ondelete='CASCADE'), nullable=False)
    step_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    material = Column(JSON)
    
    # Индексы и ограничения
    __table_args__ = (
        CheckConstraint('step_number > 0', name='check_step_number'),
        Index('idx_plan_steps_plan_id', 'plan_id'),
        Index('idx_plan_steps_skill_id', 'skill_id'),
        Index('idx_plan_steps_step_number', 'step_number'),
    )

# Настройка связей после всех классов

# User связи
User.sessions = relationship('Session', back_populates='user', cascade='all, delete-orphan')
User.skills = relationship('SkillsUser', back_populates='user', cascade='all, delete-orphan')
User.plans = relationship('Plan', back_populates='user', cascade='all, delete-orphan')

# Session связи
Session.user = relationship('User', back_populates='sessions')
Session.user_skills = relationship('SkillsUser', back_populates='session', cascade='all, delete-orphan')
Session.position_skills = relationship('SkillsPosition', back_populates='session', cascade='all, delete-orphan')
Session.plans = relationship('Plan', back_populates='session', cascade='all, delete-orphan')

# Position связи
Position.skills = relationship('SkillsPosition', back_populates='position', cascade='all, delete-orphan')

# Skill связи
Skill.users = relationship('SkillsUser', back_populates='skill', cascade='all, delete-orphan')
Skill.positions = relationship('SkillsPosition', back_populates='skill', cascade='all, delete-orphan')
Skill.plan_steps = relationship('PlanStep', back_populates='skill', cascade='all, delete-orphan')

# SkillsUser связи
SkillsUser.user = relationship('User', back_populates='skills')
SkillsUser.skill = relationship('Skill', back_populates='users')
SkillsUser.session = relationship('Session', back_populates='user_skills')

# SkillsPosition связи
SkillsPosition.session = relationship('Session', back_populates='position_skills')
SkillsPosition.position = relationship('Position', back_populates='skills')
SkillsPosition.skill = relationship('Skill', back_populates='positions')

# Plan связи
Plan.user = relationship('User', back_populates='plans')
Plan.session = relationship('Session', back_populates='plans')
Plan.steps = relationship('PlanStep', back_populates='plan', cascade='all, delete-orphan')

# PlanStep связи
PlanStep.plan = relationship('Plan', back_populates='steps')
PlanStep.skill = relationship('Skill', back_populates='plan_steps')

# Создание базы данных
if __name__ == '__main__':
    # Создаем все таблицы
    Base.metadata.create_all(engine)
    print("Database database.db successfully created")
    print("\nCreated tables:")
    for table in Base.metadata.tables.keys():
        print(f"  - {table}")
    
    # Проверка через сессию
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Проверяем, существует ли пользователь
    existing_user = session.query(User).filter_by(email="test2@example.com").first()
    
    if not existing_user:
        test_user = User(
            email="test2@example.com",
            name="Тестовый пользователь",
            password_hash="hash1234",
            registration_date=datetime.now()
        )
        session.add(test_user)
        session.commit()
        print(f"\nTest user added (id: {test_user.id})")
    else:
        print(f"\nTest user already exists (id: {existing_user.id})")
    
    session.close()