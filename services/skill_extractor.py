# -*- coding: utf-8 -*-
# services/skill_extractor.py
"""
Детерминированный экстрактор навыков из текста вакансий.
Без AI — только словарь + подсчёт частоты.
"""

import re
from collections import Counter
from typing import List, Dict, Any

# ============================================================
# Словарь навыков: ключ — паттерн для поиска (lowercase),
# значение — каноническое название навыка
# ============================================================
SKILLS_DICT = {
    # Языки программирования
    "python": "Уметь программировать на Python",
    "java": "Уметь программировать на Java",
    "javascript": "Уметь программировать на JavaScript",
    "typescript": "Уметь программировать на TypeScript",
    "c++": "Уметь программировать на C++",
    "c#": "Уметь программировать на C#",
    "golang": "Уметь программировать на Go",
    r"\bgo\b": "Уметь программировать на Go",
    "rust": "Уметь программировать на Rust",
    "php": "Уметь программировать на PHP",
    "ruby": "Уметь программировать на Ruby",
    "swift": "Уметь программировать на Swift",
    "kotlin": "Уметь программировать на Kotlin",
    "scala": "Уметь программировать на Scala",
    "r language": "Уметь работать с R",
    r"\bmatlab\b": "Уметь работать с MATLAB",
    "1c": "Уметь программировать на 1C",
    "1с": "Уметь программировать на 1C",

    # Python фреймворки и библиотеки
    "django": "Уметь разрабатывать на Django",
    "flask": "Уметь разрабатывать на Flask",
    "fastapi": "Уметь разрабатывать на FastAPI",
    "aiohttp": "Уметь работать с aiohttp",
    "sqlalchemy": "Уметь работать с SQLAlchemy",
    "pandas": "Уметь работать с Pandas",
    "numpy": "Уметь работать с NumPy",
    "scipy": "Уметь работать с SciPy",
    "matplotlib": "Уметь строить графики в Matplotlib",
    "seaborn": "Уметь визуализировать данные в Seaborn",
    "scikit-learn": "Уметь работать с Scikit-learn",
    "sklearn": "Уметь работать с Scikit-learn",
    "tensorflow": "Уметь работать с TensorFlow",
    "pytorch": "Уметь работать с PyTorch",
    "keras": "Уметь работать с Keras",
    "xgboost": "Уметь работать с XGBoost",
    "lightgbm": "Уметь работать с LightGBM",
    "catboost": "Уметь работать с CatBoost",
    "celery": "Уметь настраивать Celery",
    "pydantic": "Уметь использовать Pydantic",
    "asyncio": "Понимать асинхронное программирование (asyncio)",

    # JS/TS фреймворки
    "react": "Уметь разрабатывать на React",
    "vue": "Уметь разрабатывать на Vue.js",
    "angular": "Уметь разрабатывать на Angular",
    "next.js": "Уметь разрабатывать на Next.js",
    "nextjs": "Уметь разрабатывать на Next.js",
    "nuxt": "Уметь разрабатывать на Nuxt.js",
    "node.js": "Уметь разрабатывать на Node.js",
    "nodejs": "Уметь разрабатывать на Node.js",
    "express": "Уметь разрабатывать на Express.js",
    "webpack": "Уметь настраивать Webpack",
    "vite": "Уметь настраивать Vite",

    # Java фреймворки
    "spring": "Уметь работать со Spring",
    "spring boot": "Уметь работать со Spring Boot",
    "hibernate": "Уметь работать с Hibernate",
    "maven": "Уметь работать с Maven",
    "gradle": "Уметь работать с Gradle",

    # Базы данных
    r"\bsql\b": "Уметь писать SQL-запросы",
    "postgresql": "Уметь работать с PostgreSQL",
    "postgres": "Уметь работать с PostgreSQL",
    "mysql": "Уметь работать с MySQL",
    "sqlite": "Уметь работать с SQLite",
    "mongodb": "Уметь работать с MongoDB",
    "redis": "Уметь работать с Redis",
    "elasticsearch": "Уметь работать с Elasticsearch",
    "clickhouse": "Уметь работать с ClickHouse",
    "oracle": "Уметь работать с Oracle DB",
    "cassandra": "Уметь работать с Cassandra",
    "neo4j": "Уметь работать с Neo4j",
    "mssql": "Уметь работать с MS SQL",
    "sql server": "Уметь работать с MS SQL",

    # DevOps и инфраструктура
    "docker": "Уметь работать с Docker",
    "kubernetes": "Уметь работать с Kubernetes",
    r"\bk8s\b": "Уметь работать с Kubernetes",
    "terraform": "Уметь работать с Terraform",
    "ansible": "Уметь работать с Ansible",
    "jenkins": "Уметь настраивать Jenkins",
    "gitlab ci": "Уметь настраивать GitLab CI/CD",
    "github actions": "Уметь настраивать GitHub Actions",
    "ci/cd": "Понимать принципы CI/CD",
    "nginx": "Уметь настраивать Nginx",
    "apache": "Уметь настраивать Apache",
    "linux": "Уметь работать в Linux",
    r"\bbash\b": "Уметь писать Bash-скрипты",
    "shell": "Уметь работать с командной строкой",

    # Облака
    r"\baws\b": "Уметь работать с AWS",
    "amazon web services": "Уметь работать с AWS",
    r"\bazure\b": "Уметь работать с Azure",
    r"\bgcp\b": "Уметь работать с GCP",
    "google cloud": "Уметь работать с GCP",
    "yandex cloud": "Уметь работать с Yandex Cloud",
    "s3": "Уметь работать с AWS S3",

    # Очереди и стриминг
    "kafka": "Уметь работать с Apache Kafka",
    "rabbitmq": "Уметь работать с RabbitMQ",
    "airflow": "Уметь работать с Apache Airflow",
    "spark": "Уметь работать с Apache Spark",
    "hadoop": "Уметь работать с Hadoop",

    # API и протоколы
    "rest api": "Уметь проектировать REST API",
    "restful": "Уметь проектировать REST API",
    r"\brest\b": "Уметь проектировать REST API",
    "graphql": "Уметь работать с GraphQL",
    r"\bgrpc\b": "Уметь работать с gRPC",
    "websocket": "Уметь работать с WebSocket",
    "openapi": "Уметь документировать API через OpenAPI",
    "swagger": "Уметь документировать API через Swagger",

    # Тестирование
    "pytest": "Уметь писать тесты на pytest",
    "unittest": "Уметь писать тесты на unittest",
    "selenium": "Уметь автоматизировать тестирование в Selenium",
    "postman": "Уметь тестировать API в Postman",
    "jest": "Уметь писать тесты на Jest",
    "cypress": "Уметь писать тесты на Cypress",

    # Инструменты разработки
    r"\bgit\b": "Уметь работать с Git",
    "github": "Уметь работать с GitHub",
    "gitlab": "Уметь работать с GitLab",
    "jira": "Уметь работать в Jira",
    "confluence": "Уметь работать в Confluence",

    # Аналитика и BI
    "tableau": "Уметь визуализировать данные в Tableau",
    "power bi": "Уметь визуализировать данные в Power BI",
    "looker": "Уметь работать с Looker",
    "superset": "Уметь работать с Apache Superset",

    # ML/AI концепции
    "machine learning": "Понимать основы Machine Learning",
    "deep learning": "Понимать основы Deep Learning",
    "nlp": "Понимать основы NLP",
    "natural language processing": "Понимать основы NLP",
    "computer vision": "Понимать основы Computer Vision",
    "data science": "Понимать основы Data Science",
    "нейронные сети": "Понимать основы нейронных сетей",
    "neural network": "Понимать основы нейронных сетей",
    "llm": "Понимать принципы работы LLM",

    # Методологии
    "agile": "Понимать принципы Agile",
    "scrum": "Уметь работать по Scrum",
    "kanban": "Уметь работать по Kanban",
    r"\btdd\b": "Понимать принципы TDD",
    r"\bbdd\b": "Понимать принципы BDD",
    "микросервис": "Понимать архитектуру микросервисов",
    "microservice": "Понимать архитектуру микросервисов",

    # Веб и фронтенд
    r"\bhtml\b": "Уметь верстать на HTML",
    r"\bcss\b": "Уметь стилизовать на CSS",
    "sass": "Уметь работать с SASS/SCSS",
    "scss": "Уметь работать с SASS/SCSS",

    # Безопасность
    "oauth": "Понимать принципы OAuth",
    "jwt": "Понимать принципы JWT",
    "ssl": "Понимать принципы SSL/TLS",
    r"\btls\b": "Понимать принципы SSL/TLS",
}

# Порог для определения важности навыка.
# Навык считается обязательным если его частота >= IMPORTANCE_THRESHOLD%
# ИЛИ он входит в топ MANDATORY_TOP_N по частоте.
IMPORTANCE_THRESHOLD = 30   # абсолютный порог (%)
MANDATORY_TOP_N = 5         # минимум топ-5 навыков всегда обязательные

# ============================================================
# Список soft skills и нетехнических навыков для исключения.
# Сравнение регистронезависимое.
# ============================================================
SOFT_SKILLS = {
    # Личные качества
    "внимательность", "ответственность", "коммуникабельность", "стрессоустойчивость",
    "целеустремлённость", "целеустремленность", "инициативность", "самостоятельность",
    "обучаемость", "пунктуальность", "исполнительность", "дисциплинированность",
    "аналитическое мышление", "критическое мышление", "системное мышление",
    "внимание к деталям", "ориентация на результат", "клиентоориентированность",
    "многозадачность", "гибкость", "адаптивность", "проактивность",
    "лидерство", "лидерские качества", "эмпатия", "креативность",
    "тайм-менеджмент", "самоорганизация", "работа в команде", "teamwork",
    "коммуникация", "презентационные навыки", "навыки презентации",
    "умение работать в команде", "умение работать самостоятельно",

    # Методологии и процессы (не технические навыки)
    "scrum", "agile", "kanban", "waterfall",
    "инженерная культура", "политика тестирования",
    "анализ требований", "сбор требований",
    "код-ревью", "code review",
    "оптимизация кода", "рефакторинг кода",
    "серверное программирование",
    "управление проектами", "project management",
    "деловая переписка", "деловое общение",
    "наставничество", "менторство",
    "документирование", "техническая документация",
}


def _get_text_from_vacancy(vacancy: Dict[str, Any]) -> str:
    """Собирает весь текст из вакансии для анализа"""
    parts = []
    if vacancy.get('name'):
        parts.append(vacancy['name'])
    snippet = vacancy.get('snippet') or {}
    if snippet.get('requirement'):
        parts.append(snippet['requirement'])
    if snippet.get('responsibility'):
        parts.append(snippet['responsibility'])
    if vacancy.get('description'):
        parts.append(vacancy['description'])
    return ' '.join(parts)


def _extract_skills_from_text(text: str) -> List[str]:
    """Извлекает навыки из одного текста по словарю"""
    if not text:
        return []
    text_lower = text.lower()
    found = set()
    for pattern, canonical_name in SKILLS_DICT.items():
        if re.search(pattern, text_lower):
            found.add(canonical_name)
    return list(found)


def _is_hard_skill(name: str) -> bool:
    """Возвращает True если навык является хард-скиллом (не soft skill)."""
    return name.strip().lower() not in SOFT_SKILLS


def extract_skills_from_vacancies(
    vacancies_data: Dict[str, Any],
    top_n: int = 25
) -> List[Dict[str, Any]]:
    """
    Основная функция: анализирует список вакансий и возвращает навыки с частотой.

    Стратегия (приоритет):
    1. key_skills из детальных страниц вакансий (точные навыки от работодателя)
    2. Для вакансий без key_skills — текстовый анализ по словарю (fallback)

    Args:
        vacancies_data: ответ от hh.ru API (dict с ключом 'items')
        top_n: сколько топ-навыков вернуть

    Returns:
        Список словарей: [{"name": str, "frequency": int, "importance": str}, ...]
        frequency — процент вакансий, где встречается навык (0-100)
        importance — "important" если >= IMPORTANCE_THRESHOLD%, иначе "not_important"
    """
    items = vacancies_data.get('items', [])
    if not items:
        return []

    total = len(items)
    skill_counter = Counter()

    for vacancy in items:
        skills_in_vacancy = set()

        # Приоритет 1: key_skills (точные навыки от работодателя)
        key_skills = vacancy.get('key_skills', [])
        if key_skills:
            for ks in key_skills:
                name = ks.get('name', '').strip()
                if name and _is_hard_skill(name):
                    skills_in_vacancy.add(name)

        # Приоритет 2: fallback — текстовый анализ по словарю
        if not skills_in_vacancy:
            text = _get_text_from_vacancy(vacancy)
            for found in _extract_skills_from_text(text):
                if _is_hard_skill(found):
                    skills_in_vacancy.add(found)

        for skill in skills_in_vacancy:
            skill_counter[skill] += 1

    result = []
    top_skills = skill_counter.most_common(top_n)

    for rank, (skill_name, count) in enumerate(top_skills):
        frequency = round((count / total) * 100)
        # Обязательный если: частота >= порога ИЛИ входит в топ-N
        if frequency >= IMPORTANCE_THRESHOLD or rank < MANDATORY_TOP_N:
            importance = "important"
        else:
            importance = "not_important"
        result.append({
            "name": skill_name,
            "frequency": frequency,
            "importance": importance
        })

    return result


def get_position_name(vacancies_data: Dict[str, Any], query: str) -> str:
    """
    Определяет название должности из данных вакансий.
    Берёт самое частое название вакансии или возвращает query.
    """
    items = vacancies_data.get('items', [])
    if not items:
        return query

    # Берём первое название как базовое (оно наиболее релевантно запросу)
    return items[0].get('name', query)
