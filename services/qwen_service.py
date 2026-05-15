# -*- coding: utf-8 -*-
# services/qwen_service.py
"""
Сервис генерации плана обучения через Groq API (llama-3.3-70b-versatile).
Без fallback на mock — если ключ не задан, возвращает ошибку.
"""

import os
import re
import json
import requests
from urllib.parse import quote
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"  # основная модель
# Лёгкая модель для отбора курсов по цели недели (только из готового списка кандидатов)
GROQ_COURSE_RANKER_MODEL = "llama-3.1-8b-instant"

# Список моделей для fallback если основная перегружена
FALLBACK_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]


# ============================================================
# ПРОМТ-НАСТАВНИК (ссылки на курсы подставляются автоматически: каталог Stepik + словарь)
# ============================================================
SYSTEM_PROMPT = """Ты — опытный наставник по IT-карьере и персональный ментор по обучению.
Твоя задача — составить чёткий, реалистичный и мотивирующий план обучения для человека, который хочет стать востребованным специалистом.

Правила работы:
1. Ты говоришь как живой наставник — конкретно, по делу, без воды и шаблонных фраз.
2. Ты учитываешь реальный уровень человека, его время и цели.
3. Ты приоритизируешь навыки: сначала самые важные для рынка труда, потом дополнительные.
4. Ты разбиваешь план по неделям — реалистично, без перегрузки.
5. Ты честен: если срок слишком короткий для всех навыков — говоришь об этом и расставляешь приоритеты.
6. Ты всегда отвечаешь строго в формате JSON — без пояснений до или после.
7. НЕ включай поле "resources" в ответ — ресурсы будут добавлены автоматически."""


def generate_learning_plan(
    job_title: str,
    deficit_skills: List[Dict[str, Any]],
    level: str,
    period: str,
    time_per_day: str,
    payment_type: str
) -> Dict[str, Any]:
    """
    Генерирует план обучения через Qwen.

    Args:
        job_title: целевая должность
        deficit_skills: навыки которые пользователь не знает
            [{"name": str, "frequency": int, "importance": str}, ...]
        level: желаемый уровень (minimal/middle/advanced/very_high)
        period: срок обучения (например "3 месяца")
        time_per_day: минут в день ("30"/"60"/"120"/"180")
        payment_type: тип ресурсов ("free"/"paid"/"mixed")

    Returns:
        dict с полями "title", "summary", "weeks"

    Raises:
        RuntimeError: если API недоступен или ключ не задан
    """
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY не задан. "
            "Добавьте его в файл .env: GROQ_API_KEY=ваш_ключ"
        )

    # Формируем читаемые описания
    level_labels = {
        "minimal": "минимальный (базовые знания для старта)",
        "middle": "средний (уверенный junior/middle)",
        "advanced": "продвинутый (senior-уровень)",
        "very_high": "экспертный (tech lead / архитектор)"
    }
    time_labels = {
        "30": "30–40 минут в день",
        "60": "1–2 часа в день",
        "120": "3–4 часа в день",
        "180": "5+ часов в день"
    }
    payment_labels = {
        "free": "только бесплатные ресурсы",
        "paid": "платные курсы приветствуются",
        "mixed": "mix бесплатных и платных ресурсов"
    }

    # Список навыков для промта
    mandatory = [s for s in deficit_skills if s.get("importance") == "important"]
    optional = [s for s in deficit_skills if s.get("importance") != "important"]

    mandatory_text = "\n".join(
        f"  - {s['name']} (встречается в {s.get('frequency', '?')}% вакансий)"
        for s in mandatory
    ) or "  (нет)"

    optional_text = "\n".join(
        f"  - {s['name']} (встречается в {s.get('frequency', '?')}% вакансий)"
        for s in optional
    ) or "  (нет)"

    user_prompt = f"""Составь план обучения для: **{job_title}**

ПРОФИЛЬ:
- Уровень: {level_labels.get(level, level)}
- Срок: {period}
- Время в день: {time_labels.get(time_per_day, time_per_day + ' мин')}
- Ресурсы: {payment_labels.get(payment_type, payment_type)}

НАВЫКИ ДЛЯ ИЗУЧЕНИЯ:
Обязательные:
{mandatory_text}

Дополнительные:
{optional_text}

ТРЕБОВАНИЯ:
1. Максимум 8 недель — группируй навыки по несколько в неделю
2. Начни с обязательных навыков
3. В "skills" используй короткие технические названия: «Docker», «SQL», «React»
4. Цель и совет — по 1 короткому предложению
5. НЕ включай поле "resources"

Верни СТРОГО JSON без markdown:
{{
  "title": "...",
  "summary": "... (1 предложение)",
  "total_weeks": число,
  "weeks": [
    {{
      "week": 1,
      "theme": "...",
      "skills": ["навык"],
      "goal": "...",
      "mentor_tip": "..."
    }}
  ]
}}"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.4,
        "max_tokens": 3000
    }

    # Перебираем модели при 429
    last_error = None
    for model in FALLBACK_MODELS:
        payload["model"] = model
        print(f"  [Qwen] trying model: {model}")
        try:
            response = requests.post(
                GROQ_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            if response.status_code == 429:
                print(f"  [Groq] {model} rate limited, trying next...")
                last_error = f"Модель {model} перегружена"
                import time; time.sleep(1)
                continue
            response.raise_for_status()
            print(f"  [Groq] success with model: {model}")
            break
        except requests.exceptions.Timeout:
            last_error = f"Модель {model} не ответила за 90 секунд"
            continue
        except requests.exceptions.HTTPError as e:
            if response.status_code in (429, 400):
                last_error = f"Модель {model} недоступна ({response.status_code})"
                continue
            raise RuntimeError(f"Ошибка подключения к Groq: {e}")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ошибка подключения к Groq: {e}")
    else:
        print(f"  [Groq] all models rate limited, using deterministic fallback")
        return _deterministic_plan(job_title, deficit_skills, level, period, time_per_day, payment_type)

    data = response.json()

    # Извлекаем контент
    try:
        content = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Неожиданный формат ответа от Groq: {data}")

    # Убираем markdown-блоки если модель всё же добавила
    if "```" in content:
        parts = content.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                content = part
                break

    # Парсим JSON
    try:
        plan = json.loads(content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Groq вернул невалидный JSON: {e}\nОтвет: {content[:300]}")

    # Валидация структуры
    if "weeks" not in plan:
        raise RuntimeError("В ответе Qwen отсутствует поле 'weeks'")
    if "title" not in plan:
        plan["title"] = f"План обучения: {job_title}"
    if "summary" not in plan:
        plan["summary"] = "Следуй плану последовательно и не пропускай практику."

    # Подставляем проверенные ресурсы из словаря
    plan = _inject_resources(plan, payment_type)

    return plan


# ============================================================
# Проверенный словарь ресурсов по навыкам
# ============================================================

SKILL_RESOURCES = {
    # C++ / С++ (Stepik; словарь подстраховывает поиск)
    "c++": [
        {"title": "Программирование на языке C++ — Stepik", "url": "https://stepik.org/course/7/promo", "type": "course", "is_free": True},
        {"title": "Введение в программирование (C++) — Stepik", "url": "https://stepik.org/course/363/promo", "type": "course", "is_free": True},
        {"title": "C++ для начинающих — Stepik", "url": "https://stepik.org/course/211750/promo", "type": "course", "is_free": True},
    ],
    "cpp": [
        {"title": "Программирование на языке C++ — Stepik", "url": "https://stepik.org/course/7/promo", "type": "course", "is_free": True},
        {"title": "Введение в программирование (C++) — Stepik", "url": "https://stepik.org/course/363/promo", "type": "course", "is_free": True},
    ],
    "с++": [
        {"title": "Программирование на языке C++ — Stepik", "url": "https://stepik.org/course/7/promo", "type": "course", "is_free": True},
        {"title": "Введение в программирование (C++) — Stepik", "url": "https://stepik.org/course/363/promo", "type": "course", "is_free": True},
    ],
    # Python
    "python": [
        {"title": "«Поколение Python»: для начинающих ⭐4.9 — Stepik (300K+ студентов)", "url": "https://stepik.org/course/58852/promo", "type": "course", "is_free": True},
        {"title": "«Поколение Python»: для продвинутых ⭐4.9 — Stepik", "url": "https://stepik.org/course/68343/promo", "type": "course", "is_free": True},
        {"title": "Python: основы и применение ⭐4.6 — Stepik (Bioinformatics Institute)", "url": "https://stepik.org/course/512/promo", "type": "course", "is_free": True},
        {"title": "Официальный туториал Python (рус.)", "url": "https://docs.python.org/ru/3/tutorial/", "type": "article", "is_free": True},
        {"title": "Python — Hexlet (бесплатно)", "url": "https://ru.hexlet.io/courses/python", "type": "course", "is_free": True},
        {"title": "Real Python — практические туториалы", "url": "https://realpython.com/", "type": "article", "is_free": True},
        {"title": "Python для анализа данных ⭐4.8 — Stepik", "url": "https://stepik.org/course/114837/promo", "type": "course", "is_free": False},
    ],
    # FastAPI
    "fastapi": [
        {"title": "FastAPI — официальная документация (рус.)", "url": "https://fastapi.tiangolo.com/ru/", "type": "article", "is_free": True},
        {"title": "FastAPI: введение и практика — Habr", "url": "https://habr.com/ru/articles/596865/", "type": "article", "is_free": True},
    ],
    # Django
    "django": [
        {"title": "Django: создание веб-приложений ⭐4.7 — Stepik", "url": "https://stepik.org/course/101860/promo", "type": "course", "is_free": True},
        {"title": "Django Girls Tutorial (рус.) — проверенный учебник", "url": "https://tutorial.djangogirls.org/ru/", "type": "course", "is_free": True},
        {"title": "Django — официальная документация", "url": "https://docs.djangoproject.com/en/stable/", "type": "article", "is_free": True},
    ],
    # Flask
    "flask": [
        {"title": "Flask — официальная документация", "url": "https://flask.palletsprojects.com/en/stable/", "type": "article", "is_free": True},
        {"title": "Flask: быстрый старт — Habr", "url": "https://habr.com/ru/articles/346346/", "type": "article", "is_free": True},
    ],
    # SQL
    "sql": [
        {"title": "Интерактивный тренажёр по SQL ⭐4.9 — Stepik (100K+ студентов)", "url": "https://stepik.org/course/63054/promo", "type": "course", "is_free": True},
        {"title": "PRO SQL ⭐4.9 — Stepik (бесплатно)", "url": "https://stepik.org/course/270334/promo", "type": "course", "is_free": True},
        {"title": "SQLZoo — интерактивная практика SQL", "url": "https://sqlzoo.net/wiki/SQL_Tutorial", "type": "practice", "is_free": True},
    ],
    # PostgreSQL
    "postgresql": [
        {"title": "Интерактивный тренажёр по SQL ⭐4.9 — Stepik", "url": "https://stepik.org/course/63054/promo", "type": "course", "is_free": True},
        {"title": "PostgreSQL Tutorial — подробный справочник", "url": "https://www.postgresqltutorial.com/", "type": "article", "is_free": True},
        {"title": "PostgreSQL — официальная документация", "url": "https://www.postgresql.org/docs/current/", "type": "article", "is_free": True},
    ],
    # MySQL
    "mysql": [
        {"title": "Интерактивный тренажёр по SQL ⭐4.9 — Stepik", "url": "https://stepik.org/course/63054/promo", "type": "course", "is_free": True},
        {"title": "MySQL Tutorial — W3Schools", "url": "https://www.w3schools.com/mysql/", "type": "article", "is_free": True},
    ],
    # Git
    "git": [
        {"title": "Введение в Git ⭐4.8 — Hexlet (бесплатно)", "url": "https://ru.hexlet.io/courses/intro_to_git", "type": "course", "is_free": True},
        {"title": "Pro Git — официальная книга (рус., бесплатно)", "url": "https://git-scm.com/book/ru/v2", "type": "article", "is_free": True},
        {"title": "Git: быстрый старт ⭐4.7 — Stepik", "url": "https://stepik.org/course/3145/promo", "type": "course", "is_free": True},
    ],
    # Docker
    "docker": [
        {"title": "Docker для начинающих ⭐4.8 — Stepik", "url": "https://stepik.org/course/123300/promo", "type": "course", "is_free": True},
        {"title": "Docker — официальная документация (Get Started)", "url": "https://docs.docker.com/get-started/", "type": "article", "is_free": True},
        {"title": "Docker: полное руководство — Habr", "url": "https://habr.com/ru/articles/310460/", "type": "article", "is_free": True},
    ],
    # Kubernetes
    "kubernetes": [
        {"title": "Kubernetes — официальная документация (рус.)", "url": "https://kubernetes.io/ru/docs/home/", "type": "article", "is_free": True},
        {"title": "Kubernetes с нуля — Habr", "url": "https://habr.com/ru/articles/589415/", "type": "article", "is_free": True},
    ],
    # Linux
    "linux": [
        {"title": "Основы Linux ⭐4.7 — Stepik (50K+ студентов)", "url": "https://stepik.org/course/73/promo", "type": "course", "is_free": True},
        {"title": "Основы командной строки — Hexlet (бесплатно)", "url": "https://ru.hexlet.io/courses/cli-basics", "type": "course", "is_free": True},
        {"title": "Linux команды — Habr", "url": "https://habr.com/ru/articles/501442/", "type": "article", "is_free": True},
    ],
    # JavaScript
    "javascript": [
        {"title": "Современный учебник JavaScript — learn.javascript.ru (лучший рус. учебник)", "url": "https://learn.javascript.ru/", "type": "course", "is_free": True},
        {"title": "JavaScript — MDN Web Docs (рус.)", "url": "https://developer.mozilla.org/ru/docs/Web/JavaScript/Guide", "type": "article", "is_free": True},
        {"title": "JavaScript — Hexlet (бесплатно)", "url": "https://ru.hexlet.io/courses/javascript-basics", "type": "course", "is_free": True},
    ],
    # TypeScript
    "typescript": [
        {"title": "TypeScript — официальная документация", "url": "https://www.typescriptlang.org/docs/", "type": "article", "is_free": True},
        {"title": "TypeScript Deep Dive — бесплатная книга (рус.)", "url": "https://basarat.gitbook.io/typescript/", "type": "article", "is_free": True},
        {"title": "TypeScript: введение — Habr", "url": "https://habr.com/ru/articles/663964/", "type": "article", "is_free": True},
    ],
    # React
    "react": [
        {"title": "React — официальная документация (рус.)", "url": "https://ru.react.dev/learn", "type": "article", "is_free": True},
        {"title": "React: полный курс ⭐4.8 — Stepik", "url": "https://stepik.org/course/107878/promo", "type": "course", "is_free": True},
        {"title": "React — Hexlet (бесплатно)", "url": "https://ru.hexlet.io/courses/js-react", "type": "course", "is_free": True},
    ],
    # Vue
    "vue": [
        {"title": "Vue.js — официальная документация (рус.)", "url": "https://ru.vuejs.org/guide/introduction.html", "type": "article", "is_free": True},
        {"title": "Vue.js — официальный интерактивный туториал", "url": "https://ru.vuejs.org/tutorial/", "type": "practice", "is_free": True},
        {"title": "Vue.js: введение — Habr", "url": "https://habr.com/ru/articles/350042/", "type": "article", "is_free": True},
    ],
    # Angular
    "angular": [
        {"title": "Angular — официальная документация", "url": "https://angular.dev/overview", "type": "article", "is_free": True},
        {"title": "Angular: введение — Habr", "url": "https://habr.com/ru/articles/348818/", "type": "article", "is_free": True},
    ],
    # Node.js
    "node": [
        {"title": "Node.js — официальная документация", "url": "https://nodejs.org/ru/docs/", "type": "article", "is_free": True},
        {"title": "Node.js — Hexlet (бесплатно)", "url": "https://ru.hexlet.io/courses/nodejs", "type": "course", "is_free": True},
    ],
    # Redis
    "redis": [
        {"title": "Redis — официальная документация", "url": "https://redis.io/docs/latest/", "type": "article", "is_free": True},
        {"title": "Redis: введение — Habr", "url": "https://habr.com/ru/articles/204354/", "type": "article", "is_free": True},
    ],
    # Machine Learning
    "machine learning": [
        {"title": "Машинное обучение ⭐4.8 — Stepik (ВШЭ, 50K+ студентов)", "url": "https://stepik.org/course/4852/promo", "type": "course", "is_free": True},
        {"title": "Intro to Machine Learning — Kaggle (практика, бесплатно)", "url": "https://www.kaggle.com/learn/intro-to-machine-learning", "type": "practice", "is_free": True},
        {"title": "Scikit-learn — официальная документация", "url": "https://scikit-learn.org/stable/user_guide.html", "type": "article", "is_free": True},
    ],
    # Deep Learning
    "deep learning": [
        {"title": "Intro to Deep Learning — Kaggle (практика, бесплатно)", "url": "https://www.kaggle.com/learn/intro-to-deep-learning", "type": "practice", "is_free": True},
        {"title": "PyTorch — официальные туториалы", "url": "https://pytorch.org/tutorials/", "type": "article", "is_free": True},
        {"title": "Deep Learning: введение — Habr", "url": "https://habr.com/ru/articles/456738/", "type": "article", "is_free": True},
    ],
    # Pandas
    "pandas": [
        {"title": "Pandas — официальная документация (User Guide)", "url": "https://pandas.pydata.org/docs/user_guide/index.html", "type": "article", "is_free": True},
        {"title": "Pandas — Kaggle (практика, бесплатно)", "url": "https://www.kaggle.com/learn/pandas", "type": "practice", "is_free": True},
    ],
    # NumPy
    "numpy": [
        {"title": "NumPy — официальная документация", "url": "https://numpy.org/doc/stable/user/quickstart.html", "type": "article", "is_free": True},
        {"title": "NumPy — Kaggle (практика, бесплатно)", "url": "https://www.kaggle.com/learn/intro-to-machine-learning", "type": "practice", "is_free": True},
    ],
    # Data Science
    "data science": [
        {"title": "Data Science на Stepik", "url": "https://stepik.org/course/4852/promo", "type": "course", "is_free": True},
        {"title": "Kaggle — практика Data Science", "url": "https://www.kaggle.com/learn", "type": "practice", "is_free": True},
        {"title": "Data Science на Habr", "url": "https://habr.com/ru/hubs/data_science/", "type": "article", "is_free": True},
    ],
    # Алгоритмы
    "алгоритм": [
        {"title": "Алгоритмы: теория и практика ⭐4.8 — Stepik (CS Center)", "url": "https://stepik.org/course/217/promo", "type": "course", "is_free": True},
        {"title": "LeetCode — практика алгоритмов (бесплатно)", "url": "https://leetcode.com/problemset/", "type": "practice", "is_free": True},
    ],
    "leetcode": [
        {"title": "LeetCode — практика алгоритмов (бесплатно)", "url": "https://leetcode.com/problemset/", "type": "practice", "is_free": True},
        {"title": "Алгоритмы: теория и практика ⭐4.8 — Stepik", "url": "https://stepik.org/course/217/promo", "type": "course", "is_free": True},
    ],
    # CSS
    "css": [
        {"title": "CSS — MDN Web Docs (рус., лучший справочник)", "url": "https://developer.mozilla.org/ru/docs/Web/CSS", "type": "article", "is_free": True},
        {"title": "Flexbox Froggy — игра для изучения Flexbox (рус.)", "url": "https://flexboxfroggy.com/#ru", "type": "practice", "is_free": True},
        {"title": "CSS Grid Garden — игра для изучения Grid (рус.)", "url": "https://cssgridgarden.com/#ru", "type": "practice", "is_free": True},
    ],
    # HTML
    "html": [
        {"title": "HTML — MDN Web Docs (рус., лучший справочник)", "url": "https://developer.mozilla.org/ru/docs/Web/HTML", "type": "article", "is_free": True},
        {"title": "HTML и CSS — Hexlet (бесплатно)", "url": "https://ru.hexlet.io/courses/html", "type": "course", "is_free": True},
    ],
    # Java
    "java": [
        {"title": "Практический тренажёр по Java ⭐4.9 — Stepik (19K+ студентов)", "url": "https://stepik.org/course/182389/promo", "type": "course", "is_free": False},
        {"title": "Java. Базовый курс ⭐4.7 — Stepik (бесплатно)", "url": "https://stepik.org/course/187/promo", "type": "course", "is_free": True},
        {"title": "Java — официальная документация Oracle", "url": "https://docs.oracle.com/en/java/", "type": "article", "is_free": True},
    ],
    # Spring
    "spring": [
        {"title": "Spring — официальные гайды", "url": "https://spring.io/guides", "type": "article", "is_free": True},
        {"title": "Spring Boot: введение — Habr", "url": "https://habr.com/ru/articles/490586/", "type": "article", "is_free": True},
    ],
    # C#
    "c#": [
        {"title": "C# — Microsoft Learn (рус., официальный курс)", "url": "https://learn.microsoft.com/ru-ru/dotnet/csharp/tour-of-csharp/", "type": "course", "is_free": True},
        {"title": "C# для начинающих ⭐4.8 — Stepik", "url": "https://stepik.org/course/62085/promo", "type": "course", "is_free": True},
    ],
    # .NET
    ".net": [
        {"title": ".NET — Microsoft Learn (рус., официальный курс)", "url": "https://learn.microsoft.com/ru-ru/dotnet/", "type": "article", "is_free": True},
        {"title": "ASP.NET Core: введение — Habr", "url": "https://habr.com/ru/articles/461433/", "type": "article", "is_free": True},
    ],
    # Go
    "go": [
        {"title": "Go — официальный интерактивный туториал (A Tour of Go)", "url": "https://go.dev/tour/welcome/1", "type": "course", "is_free": True},
        {"title": "Go — официальная документация", "url": "https://go.dev/doc/", "type": "article", "is_free": True},
    ],
    "golang": [
        {"title": "Go — официальный интерактивный туториал (A Tour of Go)", "url": "https://go.dev/tour/welcome/1", "type": "course", "is_free": True},
        {"title": "Go — официальная документация", "url": "https://go.dev/doc/", "type": "article", "is_free": True},
    ],
    # Rust
    "rust": [
        {"title": "The Rust Book — официальная книга (рус.)", "url": "https://doc.rust-lang.ru/book/", "type": "article", "is_free": True},
        {"title": "Rustlings — интерактивные упражнения (бесплатно)", "url": "https://github.com/rust-lang/rustlings", "type": "practice", "is_free": True},
    ],
    # CI/CD
    "ci/cd": [
        {"title": "GitHub Actions — официальная документация (рус.)", "url": "https://docs.github.com/ru/actions", "type": "article", "is_free": True},
        {"title": "CI/CD: введение — Habr", "url": "https://habr.com/ru/articles/508216/", "type": "article", "is_free": True},
    ],
    "github actions": [
        {"title": "GitHub Actions — официальная документация (рус.)", "url": "https://docs.github.com/ru/actions", "type": "article", "is_free": True},
        {"title": "GitHub Actions: практика — Habr", "url": "https://habr.com/ru/articles/476368/", "type": "article", "is_free": True},
    ],
    # Figma / UI/UX
    "figma": [
        {"title": "Figma — официальное обучение (Learn Design)", "url": "https://www.figma.com/resources/learn-design/", "type": "course", "is_free": True},
        {"title": "Figma для начинающих — Habr", "url": "https://habr.com/ru/articles/508124/", "type": "article", "is_free": True},
    ],
    "ui": [
        {"title": "Figma — официальное обучение (Learn Design)", "url": "https://www.figma.com/resources/learn-design/", "type": "course", "is_free": True},
        {"title": "UI/UX — Habr Hub", "url": "https://habr.com/ru/hubs/ui/", "type": "article", "is_free": True},
    ],
    "ux": [
        {"title": "Figma — официальное обучение (Learn Design)", "url": "https://www.figma.com/resources/learn-design/", "type": "course", "is_free": True},
        {"title": "UX — Habr Hub", "url": "https://habr.com/ru/hubs/ux/", "type": "article", "is_free": True},
    ],
    # Аналитика
    "tableau": [
        {"title": "Tableau — официальное бесплатное обучение", "url": "https://www.tableau.com/learn/training", "type": "course", "is_free": True},
        {"title": "Tableau: введение — Habr", "url": "https://habr.com/ru/articles/270557/", "type": "article", "is_free": True},
    ],
    "power bi": [
        {"title": "Power BI — Microsoft Learn (рус., официальный курс)", "url": "https://learn.microsoft.com/ru-ru/power-bi/fundamentals/service-get-started", "type": "course", "is_free": True},
        {"title": "Power BI: введение — Habr", "url": "https://habr.com/ru/articles/484618/", "type": "article", "is_free": True},
    ],
    # Тестирование
    "тестирование": [
        {"title": "Тестирование ПО ⭐4.7 — Stepik (30K+ студентов)", "url": "https://stepik.org/course/16478/promo", "type": "course", "is_free": True},
        {"title": "QA — Habr Hub", "url": "https://habr.com/ru/hubs/testing/", "type": "article", "is_free": True},
    ],
    "selenium": [
        {"title": "Selenium — официальная документация", "url": "https://www.selenium.dev/documentation/", "type": "article", "is_free": True},
        {"title": "Автоматизация тестирования с Selenium — Habr", "url": "https://habr.com/ru/articles/152653/", "type": "article", "is_free": True},
    ],
    "pytest": [
        {"title": "Pytest: Глубокое погружение ⭐5.0 — Stepik", "url": "https://stepik.org/course/235077/promo", "type": "course", "is_free": False},
        {"title": "Pytest — официальная документация", "url": "https://docs.pytest.org/en/stable/", "type": "article", "is_free": True},
    ],
    # C / C++
    "c++": [
        {"title": "C++ для начинающих ⭐4.8 — Stepik", "url": "https://stepik.org/course/7/promo", "type": "course", "is_free": True},
        {"title": "C++ — cppreference.com (справочник)", "url": "https://ru.cppreference.com/w/cpp", "type": "article", "is_free": True},
        {"title": "C++ на Habr", "url": "https://habr.com/ru/hubs/cpp/", "type": "article", "is_free": True},
    ],
    "c": [
        {"title": "C для начинающих ⭐4.7 — Stepik", "url": "https://stepik.org/course/57680/promo", "type": "course", "is_free": True},
        {"title": "C — cppreference.com (справочник)", "url": "https://ru.cppreference.com/w/c", "type": "article", "is_free": True},
    ],
    # 1С
    "1с": [
        {"title": "1С:Программирование для начинающих ⭐4.8 — Stepik", "url": "https://stepik.org/course/4235/promo", "type": "course", "is_free": True},
        {"title": "1С — официальная документация", "url": "https://its.1c.ru/db/v8std", "type": "article", "is_free": False},
        {"title": "1С программирование — Habr", "url": "https://habr.com/ru/hubs/1c/", "type": "article", "is_free": True},
    ],
    "1c": [
        {"title": "1С:Программирование для начинающих ⭐4.8 — Stepik", "url": "https://stepik.org/course/4235/promo", "type": "course", "is_free": True},
        {"title": "1С программирование — Habr", "url": "https://habr.com/ru/hubs/1c/", "type": "article", "is_free": True},
    ],
    # Микросервисы
    "microservices": [
        {"title": "Микросервисы: введение — Habr", "url": "https://habr.com/ru/articles/249183/", "type": "article", "is_free": True},
        {"title": "Микросервисы на практике — Habr", "url": "https://habr.com/ru/articles/327416/", "type": "article", "is_free": True},
    ],
    "микросервис": [
        {"title": "Микросервисы: введение — Habr", "url": "https://habr.com/ru/articles/249183/", "type": "article", "is_free": True},
        {"title": "Микросервисы на практике — Habr", "url": "https://habr.com/ru/articles/327416/", "type": "article", "is_free": True},
    ],
    # Kafka
    "kafka": [
        {"title": "Apache Kafka — официальная документация", "url": "https://kafka.apache.org/documentation/", "type": "article", "is_free": True},
        {"title": "Kafka на Habr", "url": "https://habr.com/ru/articles/354486/", "type": "article", "is_free": True},
    ],
    # Terraform
    "terraform": [
        {"title": "Terraform — официальная документация", "url": "https://developer.hashicorp.com/terraform/docs", "type": "article", "is_free": True},
        {"title": "Terraform на Habr", "url": "https://habr.com/ru/articles/351878/", "type": "article", "is_free": True},
    ],
    # GraphQL
    "graphql": [
        {"title": "GraphQL — официальная документация (рус.)", "url": "https://graphql.org/learn/", "type": "article", "is_free": True},
        {"title": "GraphQL на Habr", "url": "https://habr.com/ru/articles/326986/", "type": "article", "is_free": True},
    ],
    # gRPC
    "grpc": [
        {"title": "gRPC — официальная документация", "url": "https://grpc.io/docs/", "type": "article", "is_free": True},
        {"title": "gRPC на Habr", "url": "https://habr.com/ru/articles/340758/", "type": "article", "is_free": True},
    ],
    # Airflow
    "airflow": [
        {"title": "Apache Airflow — официальная документация", "url": "https://airflow.apache.org/docs/", "type": "article", "is_free": True},
        {"title": "Airflow на Habr", "url": "https://habr.com/ru/articles/512386/", "type": "article", "is_free": True},
    ],
    # RabbitMQ
    "rabbitmq": [
        {"title": "RabbitMQ — официальная документация", "url": "https://www.rabbitmq.com/tutorials", "type": "article", "is_free": True},
        {"title": "RabbitMQ на Habr", "url": "https://habr.com/ru/articles/149694/", "type": "article", "is_free": True},
    ],
    # MongoDB
    "mongodb": [
        {"title": "MongoDB — официальная документация", "url": "https://www.mongodb.com/docs/manual/", "type": "article", "is_free": True},
        {"title": "MongoDB на Habr", "url": "https://habr.com/ru/articles/144798/", "type": "article", "is_free": True},
    ],
    # Elasticsearch
    "elasticsearch": [
        {"title": "Elasticsearch — официальная документация", "url": "https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html", "type": "article", "is_free": True},
        {"title": "Elasticsearch на Habr", "url": "https://habr.com/ru/articles/280488/", "type": "article", "is_free": True},
    ],
    # Nginx
    "nginx": [
        {"title": "Nginx — официальная документация", "url": "https://nginx.org/ru/docs/", "type": "article", "is_free": True},
        {"title": "Nginx на Habr", "url": "https://habr.com/ru/articles/257119/", "type": "article", "is_free": True},
    ],
    # Архитектура
    "архитектур": [
        {"title": "Паттерны проектирования — Refactoring.Guru (рус.)", "url": "https://refactoring.guru/ru/design-patterns", "type": "article", "is_free": True},
        {"title": "Архитектура ПО на Habr", "url": "https://habr.com/ru/hubs/architecture/", "type": "article", "is_free": True},
    ],
    "паттерн": [
        {"title": "Паттерны проектирования — Refactoring.Guru (рус.)", "url": "https://refactoring.guru/ru/design-patterns", "type": "article", "is_free": True},
        {"title": "Паттерны на Habr", "url": "https://habr.com/ru/hubs/patterns/", "type": "article", "is_free": True},
    ],
    # Визуализация данных
    "визуализац": [
        {"title": "Matplotlib — официальная документация", "url": "https://matplotlib.org/stable/tutorials/index.html", "type": "article", "is_free": True},
        {"title": "Seaborn — официальная документация", "url": "https://seaborn.pydata.org/tutorial.html", "type": "article", "is_free": True},
        {"title": "Data Visualization — Kaggle (практика)", "url": "https://www.kaggle.com/learn/data-visualization", "type": "practice", "is_free": True},
    ],
    "matplotlib": [
        {"title": "Matplotlib — официальная документация", "url": "https://matplotlib.org/stable/tutorials/index.html", "type": "article", "is_free": True},
        {"title": "Matplotlib на Habr", "url": "https://habr.com/ru/articles/468295/", "type": "article", "is_free": True},
    ],
    "seaborn": [
        {"title": "Seaborn — официальная документация", "url": "https://seaborn.pydata.org/tutorial.html", "type": "article", "is_free": True},
        {"title": "Data Visualization — Kaggle", "url": "https://www.kaggle.com/learn/data-visualization", "type": "practice", "is_free": True},
    ],
    # Большие данные
    "большим объём": [
        {"title": "Apache Spark — официальная документация", "url": "https://spark.apache.org/docs/latest/", "type": "article", "is_free": True},
        {"title": "Большие данные на Habr", "url": "https://habr.com/ru/hubs/bigdata/", "type": "article", "is_free": True},
    ],
    "объём информац": [
        {"title": "Apache Spark — официальная документация", "url": "https://spark.apache.org/docs/latest/", "type": "article", "is_free": True},
        {"title": "Большие данные на Habr", "url": "https://habr.com/ru/hubs/bigdata/", "type": "article", "is_free": True},
    ],
    "объем информац": [
        {"title": "Apache Spark — официальная документация", "url": "https://spark.apache.org/docs/latest/", "type": "article", "is_free": True},
        {"title": "Большие данные на Habr", "url": "https://habr.com/ru/hubs/bigdata/", "type": "article", "is_free": True},
    ],
    "big data": [
        {"title": "Apache Spark — официальная документация", "url": "https://spark.apache.org/docs/latest/", "type": "article", "is_free": True},
        {"title": "Big Data на Habr", "url": "https://habr.com/ru/hubs/bigdata/", "type": "article", "is_free": True},
    ],
    "spark": [
        {"title": "Apache Spark — официальная документация", "url": "https://spark.apache.org/docs/latest/", "type": "article", "is_free": True},
        {"title": "Spark на Habr", "url": "https://habr.com/ru/articles/350708/", "type": "article", "is_free": True},
    ],
    # ООП
    "ооп": [
        {"title": "ООП в Python — Stepik ⭐4.8", "url": "https://stepik.org/course/68343/promo", "type": "course", "is_free": True},
        {"title": "ООП на Habr: введение", "url": "https://habr.com/ru/articles/463125/", "type": "article", "is_free": True},
    ],
    "объектно-ориентированн": [
        {"title": "ООП в Python — Stepik ⭐4.8", "url": "https://stepik.org/course/68343/promo", "type": "course", "is_free": True},
        {"title": "ООП на Habr: введение", "url": "https://habr.com/ru/articles/463125/", "type": "article", "is_free": True},
    ],
    # Статистика
    "статистик": [
        {"title": "Статистика для Data Science — Stepik ⭐4.8", "url": "https://stepik.org/course/76/promo", "type": "course", "is_free": True},
        {"title": "Statistics — Khan Academy (бесплатно)", "url": "https://www.khanacademy.org/math/statistics-probability", "type": "course", "is_free": True},
    ],
    # Математика / линейная алгебра
    "математик": [
        {"title": "Математика для Data Science — Stepik", "url": "https://stepik.org/course/95/promo", "type": "course", "is_free": True},
        {"title": "Math for ML — Khan Academy (бесплатно)", "url": "https://www.khanacademy.org/math/linear-algebra", "type": "course", "is_free": True},
    ],
    "линейная алгебра": [
        {"title": "Линейная алгебра — Khan Academy (бесплатно)", "url": "https://www.khanacademy.org/math/linear-algebra", "type": "course", "is_free": True},
        {"title": "Линейная алгебра на Stepik", "url": "https://stepik.org/course/2461/promo", "type": "course", "is_free": True},
    ],
    # Безопасность
    "безопасност": [
        {"title": "Веб-безопасность — OWASP (рус.)", "url": "https://owasp.org/www-project-top-ten/", "type": "article", "is_free": True},
        {"title": "Информационная безопасность на Habr", "url": "https://habr.com/ru/hubs/infosecurity/", "type": "article", "is_free": True},
    ],
    # Сети
    "сет": [
        {"title": "Компьютерные сети — Stepik ⭐4.7", "url": "https://stepik.org/course/58678/promo", "type": "course", "is_free": True},
        {"title": "Сети на Habr", "url": "https://habr.com/ru/hubs/network_technologies/", "type": "article", "is_free": True},
    ],
    "network": [
        {"title": "Компьютерные сети — Stepik ⭐4.7", "url": "https://stepik.org/course/58678/promo", "type": "course", "is_free": True},
        {"title": "Networking — Habr", "url": "https://habr.com/ru/hubs/network_technologies/", "type": "article", "is_free": True},
    ],
    # Практика / Pet-project
    "практик": [
        {"title": "LeetCode — практика алгоритмов (бесплатно)", "url": "https://leetcode.com/problemset/", "type": "practice", "is_free": True},
        {"title": "Kaggle — практические проекты (бесплатно)", "url": "https://www.kaggle.com/learn", "type": "practice", "is_free": True},
        {"title": "GitHub — идеи для pet-проектов", "url": "https://github.com/practical-tutorials/project-based-learning", "type": "practice", "is_free": True},
    ],
    "закреплени": [
        {"title": "LeetCode — практика и закрепление (бесплатно)", "url": "https://leetcode.com/problemset/", "type": "practice", "is_free": True},
        {"title": "Codewars — задачи для закрепления навыков", "url": "https://www.codewars.com/", "type": "practice", "is_free": True},
        {"title": "GitHub — идеи для pet-проектов", "url": "https://github.com/practical-tutorials/project-based-learning", "type": "practice", "is_free": True},
    ],
    "проект": [
        {"title": "GitHub — идеи для pet-проектов", "url": "https://github.com/practical-tutorials/project-based-learning", "type": "practice", "is_free": True},
        {"title": "Codewars — практика через задачи", "url": "https://www.codewars.com/", "type": "practice", "is_free": True},
        {"title": "LeetCode — алгоритмические задачи", "url": "https://leetcode.com/problemset/", "type": "practice", "is_free": True},
    ],
    "итог": [
        {"title": "Codewars — финальная практика", "url": "https://www.codewars.com/", "type": "practice", "is_free": True},
        {"title": "LeetCode — закрепление алгоритмов", "url": "https://leetcode.com/problemset/", "type": "practice", "is_free": True},
        {"title": "GitHub — оформи своё портфолио", "url": "https://github.com/practical-tutorials/project-based-learning", "type": "practice", "is_free": True},
    ],
    "повторени": [
        {"title": "Codewars — повторение через задачи", "url": "https://www.codewars.com/", "type": "practice", "is_free": True},
        {"title": "LeetCode — практика алгоритмов", "url": "https://leetcode.com/problemset/", "type": "practice", "is_free": True},
    ],
    # API / Agile
    "api": [
        {"title": "REST API: введение — Habr", "url": "https://habr.com/ru/articles/483202/", "type": "article", "is_free": True},
        {"title": "Postman — официальное обучение", "url": "https://learning.postman.com/docs/getting-started/introduction/", "type": "article", "is_free": True},
    ],
    "agile": [
        {"title": "Scrum Guide (рус.) — официальный гайд", "url": "https://scrumguides.org/docs/scrumguide/v2020/2020-Scrum-Guide-Russian.pdf", "type": "article", "is_free": True},
        {"title": "Agile и Scrum — Habr", "url": "https://habr.com/ru/articles/247319/", "type": "article", "is_free": True},
    ],
    "scrum": [
        {"title": "Scrum Guide (рус.) — официальный гайд", "url": "https://scrumguides.org/docs/scrumguide/v2020/2020-Scrum-Guide-Russian.pdf", "type": "article", "is_free": True},
        {"title": "Scrum — Habr", "url": "https://habr.com/ru/articles/247319/", "type": "article", "is_free": True},
    ],
}

# Ресурсы по умолчанию если навык не найден в словаре
DEFAULT_RESOURCES = [
    {"title": "Каталог курсов Stepik", "url": "https://stepik.org/catalog", "type": "course", "is_free": True},
    {"title": "Бесплатные треки Kaggle Learn", "url": "https://www.kaggle.com/learn", "type": "practice", "is_free": True},
    {"title": "Статьи и хабы на Habr", "url": "https://habr.com/ru/", "type": "article", "is_free": True},
]

# Максимум ссылок на одну неделю (после слияния кураторских + поисковых)
MAX_RESOURCES_PER_WEEK = 8

TIME_LABELS = {"30": "30–40 мин/день", "60": "1–2 ч/день", "120": "3–4 ч/день", "180": "5+ ч/день"}
LEVEL_LABELS = {"minimal": "базовый", "middle": "средний", "advanced": "продвинутый", "very_high": "экспертный"}

_DEFAULT_URLS = frozenset(r["url"] for r in DEFAULT_RESOURCES)


def _skill_has_curated(skill_name: str) -> bool:
    """Есть ли в словаре проверенные материалы под этот навык (точное или частичное совпадение)."""
    key = str(skill_name).lower().strip()
    if not key:
        return False
    if key in SKILL_RESOURCES:
        return True
    return any((k in key or key in k) for k in SKILL_RESOURCES)


def _catalog_links_for_query(query: str) -> List[Dict[str, Any]]:
    """Конкретные URL поиска по запросу — если навыка нет в словаре, всё равно есть куда перейти."""
    q_raw = (query or "").strip()
    if len(q_raw) < 2:
        return []
    q_enc = quote(q_raw)
    return [
        {
            "title": f"Курсы на Stepik: «{q_raw}»",
            "url": f"https://stepik.org/catalog/search?search={q_enc}",
            "type": "course",
            "is_free": True,
        },
        {
            "title": f"Статьи на Habr: «{q_raw}»",
            "url": f"https://habr.com/ru/search/?q={q_enc}&target_type=posts&order=relevance",
            "type": "article",
            "is_free": True,
        },
        {
            "title": f"Видео на YouTube: «{q_raw}»",
            "url": f"https://www.youtube.com/results?search_query={q_enc}",
            "type": "video",
            "is_free": True,
        },
    ]


def _fallback_queries_for_week(week: Dict[str, Any]) -> List[str]:
    """Запросы для подбора ссылок: навыки недели, иначе ключевые слова из темы/цели."""
    skills = week.get("skills") or []
    out: List[str] = []
    seen: set[str] = set()
    for s in skills:
        t = str(s).strip()
        if not t:
            continue
        low = t.lower()
        if low not in seen:
            seen.add(low)
            out.append(t)
    if out:
        return out

    blob_parts = []
    for key in ("theme", "goal"):
        val = week.get(key)
        if isinstance(val, str) and val.strip():
            blob_parts.append(val.strip())
    blob = " ".join(blob_parts).strip()
    if not blob:
        return []

    stop = {
        "и", "на", "по", "для", "в", "во", "из", "к", "ко", "о", "об", "от", "до", "при",
        "это", "как", "что", "или", "the", "a", "an", "to", "of", "in", "and",
    }
    tokens = re.split(r"[\s,;.!?|—\-–]+", blob)
    uniq: List[str] = []
    for raw in tokens:
        t = raw.strip()
        if len(t) < 3 or t.lower() in stop:
            continue
        low = t.lower()
        if low not in seen:
            seen.add(low)
            uniq.append(t)
    uniq.sort(key=len, reverse=True)
    if uniq:
        return uniq[:5]
    return [blob[:50]] if blob else []


def _append_unique(resources: List[Dict[str, Any]], seen_urls: set, new_items: List[Dict[str, Any]], limit: int) -> None:
    for res in new_items:
        if len(resources) >= limit:
            return
        url = res.get("url")
        if not url or url in seen_urls:
            continue
        resources.append(res)
        seen_urls.add(url)


def _find_resources(skill_name: str, payment_type: str) -> list:
    """Ищет ресурсы для навыка в словаре. Если не найдено — генерирует ссылки на поиск по навыку."""
    key = str(skill_name).lower().strip()

    # Точное совпадение
    if key in SKILL_RESOURCES:
        resources = list(SKILL_RESOURCES[key])
    else:
        # Частичное совпадение
        match = next(
            (list(v) for k, v in SKILL_RESOURCES.items() if k in key or key in k),
            None
        )
        if match:
            resources = match
        else:
            # Навык не в словаре — генерируем ссылки на поиск по конкретному навыку
            from urllib.parse import quote
            q = quote(skill_name)
            resources = [
                {
                    "title": f"{skill_name} — курсы на Stepik",
                    "url": f"https://stepik.org/search?query={q}",
                    "type": "course",
                    "is_free": True
                },
                {
                    "title": f"{skill_name} — статьи на Habr",
                    "url": f"https://habr.com/ru/search/?q={q}&target_type=posts",
                    "type": "article",
                    "is_free": True
                },
            ]

    # Фильтрация по типу оплаты
    if payment_type == "free":
        filtered = [r for r in resources if r.get("is_free", True)]
        resources = filtered if filtered else resources
    elif payment_type == "paid":
        paid = [r for r in resources if not r.get("is_free", True)]
        resources = paid if paid else resources

    return resources[:2]


def _groq_pick_courses_for_goal(
    week: Dict[str, Any], candidates: List[Dict[str, Any]], want: int = 4
) -> List[Dict[str, Any]]:
    """
    LLM выбирает несколько курсов только из переданного списка (реальные URL + метрики отзывов).
    Не генерирует новых ссылок — только номера позиций в списке.
    """
    if not candidates:
        return []
    if len(candidates) <= want:
        return candidates[:want]
    if not GROQ_API_KEY:
        return candidates[:want]

    goal = str(week.get("goal") or "").strip()
    theme = str(week.get("theme") or "").strip()
    skills_s = ", ".join(str(s) for s in (week.get("skills") or []))
    lines: List[str] = []
    for i, c in enumerate(candidates[:10]):
        tl = (c.get("title") or "").replace(" — Stepik", "")[:160]
        ra = c.get("rating_avg")
        rn = int(c.get("rating_n") or 0)
        lc = int(c.get("learners_count") or 0)
        if ra is not None:
            rev = f"оценка ~{ra}/5 по {rn} отзывам в выборке"
        else:
            rev = "оценки по выборке нет"
        lines.append(f"{i}. {tl} | {rev} | студентов ≈{lc}")

    user = f"""Неделя учебного плана.

Цель: {goal}
Тема: {theme}
Навыки: {skills_s}

Кандидаты — только реальные курсы Stepik (номера от 0 до {len(lines) - 1}):
{chr(10).join(lines)}

Выбери ровно {want} номеров: максимально соответствуют формулировке цели недели и сочетанию «релевантность теме + хорошие отзывы + разумное число студентов».
Не добавляй курсы вне списка. Не придумывай ссылки.

Ответь строго JSON: {{"picked": [целые числа]}}"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_COURSE_RANKER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Ты помогаешь выбрать учебные курсы. Отвечай только JSON без markdown и пояснений.",
            },
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "max_tokens": 200,
    }
    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=25)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()
    except (requests.RequestException, KeyError, IndexError, ValueError):
        return candidates[:want]

    if "```" in content:
        for part in content.split("```"):
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                content = part
                break

    try:
        data = json.loads(content)
        picked = data.get("picked") or data.get("indices") or data.get("courses")
        if not isinstance(picked, list):
            return candidates[:want]
        out: List[Dict[str, Any]] = []
        seen_i: set = set()
        for raw in picked:
            try:
                i = int(raw)
            except (TypeError, ValueError):
                continue
            if i < 0 or i >= len(candidates) or i in seen_i:
                continue
            seen_i.add(i)
            out.append(candidates[i])
            if len(out) >= want:
                break
        if len(out) < want:
            for c in candidates:
                if c in out:
                    continue
                out.append(c)
                if len(out) >= want:
                    break
        return out[:want]
    except (json.JSONDecodeError, TypeError):
        return candidates[:want]


def _get_all_resources(skill_name: str) -> List[Dict[str, Any]]:
    """Возвращает ВСЕ ресурсы для навыка. Если не в словаре — поиск по навыку."""
    from urllib.parse import quote
    import re
    key = str(skill_name).lower().strip()

    # Точное совпадение
    if key in SKILL_RESOURCES:
        return list(SKILL_RESOURCES[key])

    # Частичное совпадение — короткие ключи только по границе слова
    match = None
    for k, v in SKILL_RESOURCES.items():
        if len(k) <= 2:
            if k == key or re.search(r'\b' + re.escape(k) + r'\b', key):
                match = list(v)
                break
        else:
            if k in key or key in k:
                match = list(v)
                break

    if match:
        return match

    # Навык не в словаре — конкретные ссылки на поиск (не каталог)
    from urllib.parse import quote
    q = quote(skill_name)
    q_ru = quote(skill_name + " программирование")
    return [
        {
            "title": f"{skill_name} — статьи на Habr",
            "url": f"https://habr.com/ru/search/?q={q}&target_type=posts",
            "type": "article",
            "is_free": True
        },
        {
            "title": f"{skill_name} — курсы на Coursera",
            "url": f"https://www.coursera.org/search?query={q}",
            "type": "course",
            "is_free": False
        },
    ]


# Ресурсы для недель без конкретных навыков (практика, закрепление, итог)
_PRACTICE_RESOURCES = [
    {"title": "LeetCode — практика алгоритмов (бесплатно)", "url": "https://leetcode.com/problemset/", "type": "practice", "is_free": True},
    {"title": "Codewars — задачи для закрепления навыков", "url": "https://www.codewars.com/", "type": "practice", "is_free": True},
    {"title": "GitHub — идеи для pet-проектов", "url": "https://github.com/practical-tutorials/project-based-learning", "type": "practice", "is_free": True},
    {"title": "Kaggle — практические проекты (бесплатно)", "url": "https://www.kaggle.com/learn", "type": "practice", "is_free": True},
]

_PRACTICE_KEYWORDS = {"практик", "закреплени", "проект", "итог", "повторени", "финал", "резюм", "portfolio", "портфол"}


def _inject_resources(plan: dict, payment_type: str) -> dict:
    """
    Подставляет ресурсы из словаря.
    - Один URL не повторяется во всём плане
    - Для каждого навыка берём следующий незанятый ресурс по порядку
    - Если навыков нет — определяем тип недели по теме и даём практические ресурсы
    """
    used_urls: set = set()
    skill_offset: dict = {}
    practice_offset: int = 0

    for week in plan.get("weeks", []):
        skills = week.get("skills", [])
        theme = str(week.get("theme", "")).lower()
        goal = str(week.get("goal", "")).lower()
        resources: List[Dict[str, Any]] = []
        week_urls: set = set()

        # Если навыков нет или тема — практика/закрепление
        is_practice_week = (
            not skills or
            any(kw in theme for kw in _PRACTICE_KEYWORDS) or
            any(kw in goal for kw in _PRACTICE_KEYWORDS)
        )

        if is_practice_week and not skills:
            # Берём практические ресурсы по очереди
            for i in range(min(3, len(_PRACTICE_RESOURCES))):
                idx = (practice_offset + i) % len(_PRACTICE_RESOURCES)
                res = _PRACTICE_RESOURCES[idx]
                if res["url"] not in used_urls and res["url"] not in week_urls:
                    resources.append(res)
                    used_urls.add(res["url"])
                    week_urls.add(res["url"])
                    practice_offset = idx + 1
                    if len(resources) >= 2:
                        break
        else:
            for skill in skills:
                key = skill.lower().strip()
                all_res = _get_all_resources(skill)

                if payment_type == "free":
                    preferred = [r for r in all_res if r.get("is_free", True)] or all_res
                elif payment_type == "paid":
                    preferred = [r for r in all_res if not r.get("is_free", True)] or all_res
                else:
                    preferred = all_res

                offset = skill_offset.get(key, 0)
                added = False
                for i in range(len(preferred)):
                    idx = (offset + i) % len(preferred)
                    res = preferred[idx]
                    url = res["url"]
                    if url not in used_urls and url not in week_urls:
                        resources.append(res)
                        used_urls.add(url)
                        week_urls.add(url)
                        skill_offset[key] = idx + 1
                        added = True
                        break

                if not added:
                    for res in preferred:
                        if res["url"] not in week_urls:
                            resources.append(res)
                            week_urls.add(res["url"])
                            break

        if not resources:
            # Последний резерв — практика
            for res in _PRACTICE_RESOURCES:
                if res["url"] not in week_urls:
                    resources.append(res)
                    break

        week["resources"] = resources[:3]

    return plan


def _deterministic_plan(job_title, deficit_skills, level, period, time_per_day, payment_type):
    """Генерирует план без AI — детерминированно по словарю ресурсов."""
    import math

    sorted_skills = sorted(
        deficit_skills,
        key=lambda s: (0 if s.get("importance") == "important" else 1, -s.get("frequency", 0))
    )

    period_lower = period.lower()
    if "месяц" in period_lower:
        digits = [c for c in period_lower if c.isdigit()]
        months = int("".join(digits)) if digits else 3
        total_weeks = months * 4
    elif "недел" in period_lower:
        digits = [c for c in period_lower if c.isdigit()]
        total_weeks = int("".join(digits)) if digits else 4
    else:
        total_weeks = 8

    total_weeks = max(len(sorted_skills), total_weeks)

    skills_per_week = max(1, math.ceil(len(sorted_skills) / total_weeks))
    weeks = []
    skill_idx = 0

    for week_num in range(1, total_weeks + 1):
        week_skills = []
        for _ in range(skills_per_week):
            if skill_idx < len(sorted_skills):
                week_skills.append(sorted_skills[skill_idx])
                skill_idx += 1

        if not week_skills and week_num > len(sorted_skills):
            break

        skill_names = [s["name"] for s in week_skills]
        theme = " + ".join(skill_names) if skill_names else "Повторение и практика"

        weeks.append({
            "week": week_num,
            "theme": theme,
            "skills": skill_names,
            "goal": f"Освоить {'и '.join(skill_names)} на уровне {LEVEL_LABELS.get(level, level)}",
            "mentor_tip": f"Уделяй {TIME_LABELS.get(time_per_day, time_per_day + ' мин')} и обязательно практикуйся — теория без кода не работает.",
        })

    plan = {
        "title": f"План обучения: {job_title} ({LEVEL_LABELS.get(level, level)} уровень)",
        "summary": (
            f"Ты хочешь стать {job_title} за {period}. "
            f"Перед тобой {len(sorted_skills)} навыков которые нужно освоить. "
            f"Следуй плану последовательно — каждую неделю фокусируйся на одной теме и сразу применяй на практике."
        ),
        "total_weeks": len(weeks),
        "weeks": weeks,
        "_generated_by": "deterministic_fallback"
    }

    return _inject_resources(plan, payment_type)
