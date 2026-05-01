import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import Counter

from models import SkillsPosition, Skill, SkillImportance, AnalysisMetrics, CacheEntry
from hh_parser.parse_vacancies import fetch_vacancies


class VacancyAnalysisService:
    """
    Сервис для анализа вакансий и извлечения навыков
    Курсовая работа по анализу рынка труда
    """
    
    def __init__(self, cache_duration_hours: int = 1, max_vacancies: int = 50):
        """
        Инициализация сервиса
        
        Args:
            cache_duration_hours: сколько часов хранить кэш
            max_vacancies: максимум вакансий для анализа (чтобы не перегружать)
        """
        self.cache_duration_hours = cache_duration_hours
        self.max_vacancies = max_vacancies
        self.cache: Dict[str, CacheEntry] = {}  # кэш результатов
        self.metrics: List[AnalysisMetrics] = []  # метрики производительности
        
        # Словарь навыков для поиска в вакансиях
        # Собрала самые популярные технологии из разных областей IT
        self.SKILLS = {
            # Языки программирования
            "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
            "PHP", "Ruby", "Swift", "Kotlin", "Scala",
            
            # Фреймворки и библиотеки
            "Django", "Flask", "FastAPI", "React", "Vue", "Angular", "Spring",
            "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy",
            
            # Базы данных
            "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
            "ClickHouse", "Oracle", "Cassandra",
            
            # DevOps и инструменты
            "Docker", "Kubernetes", "Git", "Linux", "Bash", "Jenkins", "GitLab CI",
            "GitHub Actions", "Nginx", "Apache", "Terraform", "Ansible",
            
            # Облачные технологии
            "AWS", "Azure", "GCP", "Yandex Cloud", "S3", "Lambda",
            
            # Тестирование
            "pytest", "unittest", "Selenium", "Postman", "JMeter",
            
            # API и протоколы
            "REST API", "GraphQL", "gRPC", "RabbitMQ", "Kafka", "Celery",
            
            # Методологии разработки
            "Agile", "Scrum", "Kanban", "CI/CD", "TDD",
            
            # Аналитика и ML
            "Machine Learning", "Data Science", "NLP", "Computer Vision",
            "Deep Learning", "Статистика", "Tableau", "Power BI"
        }
        
        # Словарь для поиска без учета регистра
        self.skills_lower = {skill.lower(): skill for skill in self.SKILLS}
        
        # Настройка логирования для отладки
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def analyze_position(self, search_query: str, area: int = 1) -> SkillsPosition:
        """
        Анализ должности: получаем вакансии с hh.ru и извлекаем навыки
        
        Args:
            search_query: Должность для поиска (например, "Data Scientist")
            area: ID региона (1 - Москва)
            
        Returns:
            SkillsPosition: результат анализа с навыками
        """
        start_time = time.time()
        
        # Сначала проверяем кэш
        cached_result = self._get_from_cache(search_query)
        if cached_result:
            self.logger.info(f"Берем результат из кэша для: {search_query}")
            return cached_result
        
        # Получаем вакансии с hh.ru
        hh_start = time.time()
        vacancies_data = fetch_vacancies(search_query, area=area, per_page=self.max_vacancies)
        hh_time = (time.time() - hh_start) * 1000
        
        # Проверяем ошибки от hh.ru
        if vacancies_data.get('error'):
            error_msg = f"Ошибка при получении вакансий: {vacancies_data.get('message')}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
        
        vacancies = vacancies_data.get('items', [])
        if not vacancies:
            self.logger.warning(f"Вакансии не найдены для: {search_query}")
            return SkillsPosition(
                position_name=search_query,
                search_query=search_query,
                total_vacancies_analyzed=0,
                skills=[]
            )
        
        # Ограничиваем количество вакансий для обработки
        vacancies = vacancies[:self.max_vacancies]
        
        # Извлекаем навыки с помощью AI
        ai_start = time.time()
        skills_data = self._extract_skills_from_vacancies(vacancies)
        ai_time = (time.time() - ai_start) * 1000
        
        # Создаем объект SkillsPosition
        skills_position = SkillsPosition(
            position_name=search_query,
            search_query=search_query,
            skills=skills_data,
            total_vacancies_analyzed=len(vacancies),
            created_at=datetime.now()
        )
        
        # Сохраняем в кэш
        self._cache_result(search_query, skills_position)
        
        # Записываем метрики
        total_time = (time.time() - start_time) * 1000
        metrics = AnalysisMetrics(
            search_query=search_query,
            hh_parsing_time_ms=hh_time,
            ai_analysis_time_ms=ai_time,
            total_time_ms=total_time,
            vacancies_found=vacancies_data.get('found', 0),
            vacancies_analyzed=len(vacancies),
            skills_extracted=len(skills_data)
        )
        self.metrics.append(metrics)
        
        self.logger.info(f"Анализ завершен для '{search_query}': "
                        f"{len(vacancies)} вакансий, {len(skills_data)} навыков, "
                        f"общее время: {total_time:.1f}мс")
        
        return skills_position
    
    def _extract_skills_from_vacancies(self, vacancies: List[Dict[str, Any]]) -> List[Skill]:
        """Extract skills from vacancy data"""
        skill_counter = Counter()
        total_vacancies = len(vacancies)
        
        for vacancy in vacancies:
            # Collect text from different fields
            text_parts = []
            
            if vacancy.get('name'):
                text_parts.append(vacancy['name'])
            
            if vacancy.get('description'):
                text_parts.append(vacancy['description'])
            
            snippet = vacancy.get('snippet', {})
            if snippet.get('requirement'):
                text_parts.append(snippet['requirement'])
            if snippet.get('responsibility'):
                text_parts.append(snippet['responsibility'])
            
            full_text = ' '.join(text_parts)
            
            # Extract skills from this vacancy
            found_skills = self._extract_skills_from_text(full_text)
            
            # Count each skill once per vacancy
            for skill in set(found_skills):
                skill_counter[skill] += 1
        
        # Convert to Skill objects with importance levels
        skills = []
        for skill_name, count in skill_counter.most_common():
            frequency = (count / total_vacancies) * 100
            
            # Determine importance based on frequency
            if frequency >= 70:
                importance = SkillImportance.MANDATORY
            elif frequency >= 40:
                importance = SkillImportance.RECOMMENDED
            else:
                importance = SkillImportance.OPTIONAL
            
            skills.append(Skill(
                name=skill_name,
                importance=importance,
                frequency=round(frequency, 1)
            ))
        
        return skills
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills from text using case-insensitive matching"""
        if not text:
            return []
        
        text = text.lower()
        found = set()
        
        for skill_key, skill_name in self.skills_lower.items():
            if skill_key in text:
                found.add(skill_name)
        
        return list(found)
    
    def _get_from_cache(self, search_query: str) -> Optional[SkillsPosition]:
        """Get cached result if available and not expired"""
        cache_entry = self.cache.get(search_query)
        if cache_entry and not cache_entry.is_expired():
            return cache_entry.position_data
        elif cache_entry and cache_entry.is_expired():
            # Remove expired entry
            del self.cache[search_query]
        return None
    
    def _cache_result(self, search_query: str, position_data: SkillsPosition):
        """Cache analysis result"""
        expires_at = datetime.now() + timedelta(hours=self.cache_duration_hours)
        cache_entry = CacheEntry(
            search_query=search_query,
            position_data=position_data,
            expires_at=expires_at
        )
        self.cache[search_query] = cache_entry
    
    def get_metrics(self) -> List[AnalysisMetrics]:
        """Get all recorded metrics"""
        return self.metrics
    
    def clear_cache(self):
        """Clear all cached results"""
        self.cache.clear()
        self.logger.info("Cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self.cache)
        expired_entries = sum(1 for entry in self.cache.values() if entry.is_expired())
        
        return {
            "total_entries": total_entries,
            "active_entries": total_entries - expired_entries,
            "expired_entries": expired_entries,
            "cache_duration_hours": self.cache_duration_hours
        }
