# -*- coding: utf-8 -*-
# DataBase.py
"""
Модели SQLAlchemy и настройка подключения к БД.
"""

import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime,
    ForeignKey, Float, Text, Boolean
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Пользователь ─────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    registration_date = Column(DateTime, default=datetime.now)

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    skills = relationship("SkillsUser", back_populates="user", cascade="all, delete-orphan")
    plans = relationship("Plan", back_populates="user", cascade="all, delete-orphan")


# ── Сессия поиска ─────────────────────────────────────────────

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    branch_type = Column(Integer, nullable=False)   # 1 = по должности, 2 = по навыкам
    search_query = Column(String(500), nullable=True)
    request_time = Column(DateTime, default=datetime.now)
    ai_result = Column(Text, nullable=True)

    user = relationship("User", back_populates="sessions")
    skills_positions = relationship("SkillsPosition", back_populates="session", cascade="all, delete-orphan")
    skills_users = relationship("SkillsUser", back_populates="session", cascade="all, delete-orphan")
    plans = relationship("Plan", back_populates="session", cascade="all, delete-orphan")


# ── Должность ────────────────────────────────────────────────

class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)

    skills_positions = relationship("SkillsPosition", back_populates="position", cascade="all, delete-orphan")


# ── Навык ────────────────────────────────────────────────────

class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)

    skills_positions = relationship("SkillsPosition", back_populates="skill", cascade="all, delete-orphan")
    skills_users = relationship("SkillsUser", back_populates="skill", cascade="all, delete-orphan")
    plan_steps = relationship("PlanStep", back_populates="skill", cascade="all, delete-orphan")


# ── Навыки должности (результат анализа HH.ru) ───────────────

class SkillsPosition(Base):
    __tablename__ = "skills_position"

    record_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    frequency = Column(Integer, nullable=True)          # % вакансий где встречается
    importance = Column(String(20), nullable=True)      # "important" / "not_important"
    analysis_date = Column(DateTime, default=datetime.now)

    session = relationship("Session", back_populates="skills_positions")
    position = relationship("Position", back_populates="skills_positions")
    skill = relationship("Skill", back_populates="skills_positions")


# ── Навыки пользователя ──────────────────────────────────────

class SkillsUser(Base):
    __tablename__ = "skills_user"

    record_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    specified_date = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="skills")
    skill = relationship("Skill", back_populates="skills_users")
    session = relationship("Session", back_populates="skills_users")


# ── План обучения ────────────────────────────────────────────

class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True)
    title = Column(String(500), nullable=True)
    created_date = Column(DateTime, default=datetime.now)
    ending_date = Column(DateTime, nullable=True)
    efficiency = Column(Float, nullable=True)
    ai_result = Column(Text, nullable=True)   # JSON плана от AI

    user = relationship("User", back_populates="plans")
    session = relationship("Session", back_populates="plans")
    steps = relationship("PlanStep", back_populates="plan", cascade="all, delete-orphan")


# ── Шаг плана ────────────────────────────────────────────────

class PlanStep(Base):
    __tablename__ = "plan_steps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    material = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False)

    plan = relationship("Plan", back_populates="steps")
    skill = relationship("Skill", back_populates="plan_steps")
