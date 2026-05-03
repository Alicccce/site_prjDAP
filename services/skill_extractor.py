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
    "python": "Python",
    "java": "Java",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "c++": "C++",
    "c#": "C#",
    "golang": "Go",
    r"\bgo\b": "Go",
    "rust": "Rust",
    "php": "PHP",
    "ruby": "Ruby",
    "swift": "Swift",
    "kotlin": "Kotlin",
    "scala": "Scala",
    "r language": "R",
    r"\bmatlab\b": "MATLAB",
    "1c": "1C",
    "1с": "1C",

    # Python фреймворки и библиотеки
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "aiohttp": "aiohttp",
    "sqlalchemy": "SQLAlchemy",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "scipy": "SciPy",
    "matplotlib": "Matplotlib",
    "seaborn": "Seaborn",
    "scikit-learn": "Scikit-learn",
    "sklearn": "Scikit-learn",
    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",
    "keras": "Keras",
    "xgboost": "XGBoost",
    "lightgbm": "LightGBM",
    "catboost": "CatBoost",
    "celery": "Celery",
    "pydantic": "Pydantic",
    "asyncio": "asyncio",

    # JS/TS фреймворки
    "react": "React",
    "vue": "Vue.js",
    "angular": "Angular",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "nuxt": "Nuxt.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "express": "Express.js",
    "webpack": "Webpack",
    "vite": "Vite",

    # Java фреймворки
    "spring": "Spring",
    "spring boot": "Spring Boot",
    "hibernate": "Hibernate",
    "maven": "Maven",
    "gradle": "Gradle",

    # Базы данных
    r"\bsql\b": "SQL",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mysql": "MySQL",
    "sqlite": "SQLite",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "elasticsearch": "Elasticsearch",
    "clickhouse": "ClickHouse",
    "oracle": "Oracle DB",
    "cassandra": "Cassandra",
    "neo4j": "Neo4j",
    "mssql": "MS SQL",
    "sql server": "MS SQL",

    # DevOps и инфраструктура
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    r"\bk8s\b": "Kubernetes",
    "terraform": "Terraform",
    "ansible": "Ansible",
    "jenkins": "Jenkins",
    "gitlab ci": "GitLab CI/CD",
    "github actions": "GitHub Actions",
    "ci/cd": "CI/CD",
    "nginx": "Nginx",
    "apache": "Apache",
    "linux": "Linux",
    r"\bbash\b": "Bash",
    "shell": "Shell",

    # Облака
    r"\baws\b": "AWS",
    "amazon web services": "AWS",
    r"\bazure\b": "Azure",
    r"\bgcp\b": "GCP",
    "google cloud": "GCP",
    "yandex cloud": "Yandex Cloud",
    "s3": "AWS S3",

    # Очереди и стриминг
    "kafka": "Apache Kafka",
    "rabbitmq": "RabbitMQ",
    "airflow": "Apache Airflow",
    "spark": "Apache Spark",
    "hadoop": "Hadoop",

    # API и протоколы
    "rest api": "REST API",
    "restful": "REST API",
    r"\brest\b": "REST API",
    "graphql": "GraphQL",
    r"\bgrpc\b": "gRPC",
    "websocket": "WebSocket",
    "openapi": "OpenAPI",
    "swagger": "Swagger",

    # Тестирование
    "pytest": "pytest",
    "unittest": "unittest",
    "selenium": "Selenium",
    "postman": "Postman",
    "jest": "Jest",
    "cypress": "Cypress",

    # Инструменты разработки
    r"\bgit\b": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",
    "jira": "Jira",
    "confluence": "Confluence",

    # Аналитика и BI
    "tableau": "Tableau",
    "power bi": "Power BI",
    "looker": "Looker",
    "superset": "Apache Superset",

    # ML/AI концепции
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "nlp": "NLP",
    "natural language processing": "NLP",
    "computer vision": "Computer Vision",
    "data science": "Data Science",
    "нейронные сети": "Neural Networks",
    "neural network": "Neural Networks",
    "llm": "LLM",

    # Методологии
    "agile": "Agile",
    "scrum": "Scrum",
    "kanban": "Kanban",
    r"\btdd\b": "TDD",
    r"\bbdd\b": "BDD",
    "микросервис": "Microservices",
    "microservice": "Microservices",

    # Веб и фронтенд
    r"\bhtml\b": "HTML",
    r"\bcss\b": "CSS",
    "sass": "SASS/SCSS",
    "scss": "SASS/SCSS",

    # Безопасность
    "oauth": "OAuth",
    "jwt": "JWT",
    "ssl": "SSL/TLS",
    r"\btls\b": "SSL/TLS",
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
