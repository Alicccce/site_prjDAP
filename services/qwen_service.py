# -*- coding: utf-8 -*-
# services/qwen_service.py
"""
Сервис генерации плана обучения через Qwen (OpenRouter API).
Без fallback на mock — если ключ не задан, возвращает ошибку.
"""

import os
import json
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
QWEN_MODEL = "meta-llama/llama-3.3-70b-instruct:free"  # основная модель

# Список моделей для fallback если основная перегружена
FALLBACK_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-coder:free",
    "google/gemma-3-27b-it:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
]


# ============================================================
# ПРОМТ-НАСТАВНИК
# ============================================================
SYSTEM_PROMPT = """Ты — опытный наставник по IT-карьере и персональный ментор по обучению.
Твоя задача — составить чёткий, реалистичный и мотивирующий план обучения для человека, который хочет стать востребованным специалистом.

Правила работы:
1. Ты говоришь как живой наставник — конкретно, по делу, без воды и шаблонных фраз.
2. Ты учитываешь реальный уровень человека, его время и цели.
3. Ты приоритизируешь навыки: сначала самые важные для рынка труда, потом дополнительные.
4. Для каждого навыка ты даёшь конкретные ресурсы — только реально существующие ссылки.
5. Ты разбиваешь план по неделям — реалистично, без перегрузки.
6. Ты честен: если срок слишком короткий для всех навыков — говоришь об этом и расставляешь приоритеты.
7. Ты всегда отвечаешь строго в формате JSON — без пояснений до или после.

Предпочитаемые ресурсы (используй в первую очередь):
- stepik.org — русскоязычные курсы
- youtube.com — видеоуроки (указывай конкретные каналы/плейлисты)
- habr.com — статьи и туториалы
- practicum.yandex.ru — Яндекс Практикум
- ru.hexlet.io — Хекслет
- realpython.com — Python туториалы
- docs.python.org — официальная документация
- developer.mozilla.org — веб-документация
- leetcode.com — практика алгоритмов
- kaggle.com — практика Data Science"""


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
    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY не задан. "
            "Добавьте его в файл .env: OPENROUTER_API_KEY=ваш_ключ"
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

    user_prompt = f"""Составь персональный план обучения для человека, который хочет стать: **{job_title}**

ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ:
- Желаемый уровень: {level_labels.get(level, level)}
- Срок обучения: {period}
- Время в день: {time_labels.get(time_per_day, time_per_day + ' мин')}
- Предпочтения по ресурсам: {payment_labels.get(payment_type, payment_type)}

НАВЫКИ КОТОРЫЕ НУЖНО ИЗУЧИТЬ:
Обязательные (требуются работодателями):
{mandatory_text}

Дополнительные (повышают шансы):
{optional_text}

ТРЕБОВАНИЯ К ПЛАНУ:
1. Раздели план по неделям — реалистично под указанное время в день
2. Начни с самых важных навыков (обязательные в первую очередь)
3. Для каждой недели укажи 1-2 конкретных ресурса со ссылками
4. Ссылки должны быть реальными и рабочими
5. Добавь краткий совет наставника для каждой недели

Верни СТРОГО JSON без markdown-блоков, без пояснений:
{{
  "title": "название плана",
  "summary": "краткое напутствие наставника (2-3 предложения)",
  "total_weeks": число,
  "weeks": [
    {{
      "week": 1,
      "theme": "тема недели",
      "skills": ["навык1", "навык2"],
      "goal": "что конкретно освоить за эту неделю",
      "mentor_tip": "совет наставника",
      "resources": [
        {{
          "title": "название ресурса",
          "url": "https://...",
          "type": "course|video|article|practice",
          "is_free": true
        }}
      ]
    }}
  ]
}}"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://dapdep.ru",
        "X-Title": "Dapdep Career Navigator"
    }

    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.4,
        "max_tokens": 4000
    }

    # Перебираем модели при 429
    last_error = None
    for model in FALLBACK_MODELS:
        payload["model"] = model
        print(f"  [Qwen] trying model: {model}")
        try:
            response = requests.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=90
            )
            if response.status_code == 429:
                print(f"  [Qwen] {model} rate limited, trying next...")
                last_error = f"Модель {model} перегружена"
                import time; time.sleep(2)
                continue
            response.raise_for_status()
            print(f"  [Qwen] success with model: {model}")
            break
        except requests.exceptions.Timeout:
            last_error = f"Модель {model} не ответила за 90 секунд"
            continue
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                last_error = f"Модель {model} перегружена"
                continue
            raise RuntimeError(f"Ошибка подключения к OpenRouter: {e}")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ошибка подключения к OpenRouter: {e}")
    else:
        print(f"  [Qwen] all models rate limited, using deterministic fallback")
        return _deterministic_plan(job_title, deficit_skills, level, period, time_per_day, payment_type)

    data = response.json()

    # Извлекаем контент
    try:
        content = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Неожиданный формат ответа от OpenRouter: {data}")

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
        raise RuntimeError(f"Qwen вернул невалидный JSON: {e}\nОтвет: {content[:300]}")

    # Валидация структуры
    if "weeks" not in plan:
        raise RuntimeError("В ответе Qwen отсутствует поле 'weeks'")
    if "title" not in plan:
        plan["title"] = f"План обучения: {job_title}"
    if "summary" not in plan:
        plan["summary"] = "Следуй плану последовательно и не пропускай практику."

    return plan


# ============================================================
# Детерминированный fallback — когда AI недоступен
# ============================================================

# Словарь ресурсов по навыкам
SKILL_RESOURCES = {
    "python": [
        {"title": "Python для начинающих — Stepik", "url": "https://stepik.org/course/67/promo", "type": "course", "is_free": True},
        {"title": "Официальная документация Python", "url": "https://docs.python.org/ru/3/tutorial/", "type": "article", "is_free": True},
    ],
    "fastapi": [
        {"title": "FastAPI — официальная документация", "url": "https://fastapi.tiangolo.com/ru/", "type": "article", "is_free": True},
        {"title": "FastAPI курс — YouTube", "url": "https://www.youtube.com/results?search_query=fastapi+курс+на+русском", "type": "video", "is_free": True},
    ],
    "docker": [
        {"title": "Docker для начинающих — Stepik", "url": "https://stepik.org/course/123300/promo", "type": "course", "is_free": True},
        {"title": "Docker — Habr", "url": "https://habr.com/ru/articles/310460/", "type": "article", "is_free": True},
    ],
    "postgresql": [
        {"title": "Интерактивный курс SQL — Stepik", "url": "https://stepik.org/course/63054/promo", "type": "course", "is_free": True},
        {"title": "PostgreSQL Tutorial", "url": "https://www.postgresqltutorial.com/", "type": "article", "is_free": True},
    ],
    "sql": [
        {"title": "Интерактивный тренажёр SQL — Stepik", "url": "https://stepik.org/course/63054/promo", "type": "course", "is_free": True},
        {"title": "SQL на W3Schools", "url": "https://www.w3schools.com/sql/", "type": "article", "is_free": True},
    ],
    "git": [
        {"title": "Git — Hexlet", "url": "https://ru.hexlet.io/courses/intro_to_git", "type": "course", "is_free": True},
        {"title": "Pro Git книга (рус.)", "url": "https://git-scm.com/book/ru/v2", "type": "article", "is_free": True},
    ],
    "linux": [
        {"title": "Linux для начинающих — Stepik", "url": "https://stepik.org/course/73/promo", "type": "course", "is_free": True},
        {"title": "Linux команды — Habr", "url": "https://habr.com/ru/articles/501442/", "type": "article", "is_free": True},
    ],
    "django": [
        {"title": "Django Girls Tutorial (рус.)", "url": "https://tutorial.djangogirls.org/ru/", "type": "course", "is_free": True},
        {"title": "Django документация", "url": "https://docs.djangoproject.com/ru/", "type": "article", "is_free": True},
    ],
    "redis": [
        {"title": "Redis — официальная документация", "url": "https://redis.io/docs/", "type": "article", "is_free": True},
        {"title": "Redis на Habr", "url": "https://habr.com/ru/articles/204354/", "type": "article", "is_free": True},
    ],
    "kubernetes": [
        {"title": "Kubernetes — официальная документация", "url": "https://kubernetes.io/ru/docs/home/", "type": "article", "is_free": True},
        {"title": "Kubernetes курс — YouTube", "url": "https://www.youtube.com/results?search_query=kubernetes+курс+русский", "type": "video", "is_free": True},
    ],
    "javascript": [
        {"title": "JavaScript — learn.javascript.ru", "url": "https://learn.javascript.ru/", "type": "course", "is_free": True},
        {"title": "JavaScript на MDN", "url": "https://developer.mozilla.org/ru/docs/Web/JavaScript", "type": "article", "is_free": True},
    ],
    "react": [
        {"title": "React — официальная документация", "url": "https://ru.react.dev/learn", "type": "article", "is_free": True},
        {"title": "React курс — Stepik", "url": "https://stepik.org/course/107878/promo", "type": "course", "is_free": True},
    ],
}

DEFAULT_RESOURCES = [
    {"title": "Поиск курсов на Stepik", "url": "https://stepik.org/catalog", "type": "course", "is_free": True},
    {"title": "Статьи на Habr", "url": "https://habr.com/ru/", "type": "article", "is_free": True},
]

TIME_LABELS = {"30": "30–40 мин/день", "60": "1–2 ч/день", "120": "3–4 ч/день", "180": "5+ ч/день"}
LEVEL_LABELS = {"minimal": "базовый", "middle": "средний", "advanced": "продвинутый", "very_high": "экспертный"}


def _deterministic_plan(job_title, deficit_skills, level, period, time_per_day, payment_type):
    """Генерирует план без AI — детерминированно по словарю ресурсов."""
    import math

    # Сортируем: сначала important, потом по frequency
    sorted_skills = sorted(
        deficit_skills,
        key=lambda s: (0 if s.get("importance") == "important" else 1, -s.get("frequency", 0))
    )

    # Определяем кол-во недель
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

    # Распределяем навыки по неделям
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

        # Ресурсы для навыков этой недели
        resources = []
        for skill in week_skills:
            key = skill["name"].lower()
            found = next(
                (v for k, v in SKILL_RESOURCES.items() if k in key or key in k),
                DEFAULT_RESOURCES
            )
            resources.extend(found[:1])  # по 1 ресурсу на навык

        if not resources:
            resources = DEFAULT_RESOURCES[:1]

        weeks.append({
            "week": week_num,
            "theme": theme,
            "skills": skill_names,
            "goal": f"Освоить {'и '.join(skill_names)} на уровне {LEVEL_LABELS.get(level, level)}",
            "mentor_tip": f"Уделяй {TIME_LABELS.get(time_per_day, time_per_day + ' мин')} и обязательно практикуйся — теория без кода не работает.",
            "resources": resources
        })

    return {
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
