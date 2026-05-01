from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class SkillImportance(Enum):
    """Уровни важности навыков"""
    MANDATORY = "mandatory"  # Обязательный
    RECOMMENDED = "recommended"  # Рекомендуемый
    OPTIONAL = "optional"  # Желательный


@dataclass
class Skill:
    """Навык с его характеристиками"""
    name: str  # Название навыка
    importance: SkillImportance  # Уровень важности
    frequency: float  # Как часто встречается в вакансиях (%)


@dataclass
class SkillsPosition:
    """Результат анализа навыков для конкретной должности"""
    id: Optional[int] = None
    position_name: str = ""  # Название должности
    skills: List[Skill] = None  # Список найденных навыков
    total_vacancies_analyzed: int = 0  # Сколько вакансий проанализировали
    created_at: datetime = None  # Когда создали запись
    search_query: str = ""  # Поисковый запрос
    
    def __post_init__(self):
        # Инициализируем списки и даты если не заданы
        if self.skills is None:
            self.skills = []
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class User:
    """Пользователь и его навыки"""
    id: Optional[int] = None
    name: str = ""  # Имя пользователя
    skills: List[str] = None  # Навыки пользователя
    created_at: datetime = None  # Когда зарегистрирован
    
    def __post_init__(self):
        if self.skills is None:
            self.skills = []
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class JobMatch:
    """Результат сравнения навыков пользователя с требованиями вакансии"""
    job_title: str  # Название должности
    match_percentage: float  # Процент совпадения
    matched_skills: List[str]  # Какие навыки совпали
    missing_skills: List[str]  # Какие навыки не хватает
    missing_mandatory: List[str]  # Обязательные навыки которые не хватает
    position_id: Optional[int] = None


@dataclass
class AnalysisMetrics:
    """Метрики производительности для анализа"""
    search_query: str  # Что искали
    hh_parsing_time_ms: float  # Время парсинга hh.ru
    ai_analysis_time_ms: float  # Время анализа AI
    total_time_ms: float  # Общее время
    vacancies_found: int  # Найдено вакансий
    vacancies_analyzed: int  # Проанализировано вакансий
    skills_extracted: int  # Извлечено навыков
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class CacheEntry:
    """Запись в кэше для недавних поисков"""
    search_query: str  # Поисковый запрос
    position_data: SkillsPosition  # Данные анализа
    expires_at: datetime  # Когда истекает кэш
    
    def is_expired(self) -> bool:
        """Проверить не истек ли кэш"""
        return datetime.now() > self.expires_at
