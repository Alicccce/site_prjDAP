# -*- coding: utf-8 -*-
# services/ai_assistant.py

import os
import json
from typing import Dict, Any, List
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


@dataclass
class AnalysisResult:
    """Result of AI vacancy analysis"""
    position_name: str
    skills: List[Dict[str, Any]]  # each skill: {"name": str, "frequency": int, "importance": str}


class AIAssistant:
    """
    AI Assistant for analyzing vacancies and generating learning plans.
    Uses OpenAI API if OPENAI_API_KEY is set, otherwise falls back to mock.
    """

    def __init__(self):
        self._client = None
        if OPENAI_API_KEY:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=OPENAI_API_KEY)
                print("[AIAssistant] OpenAI client initialized")
            except ImportError:
                print("[AIAssistant] openai package not installed, using mock")
            except Exception as e:
                print(f"[AIAssistant] OpenAI init failed: {e}, using mock")

    @property
    def _use_ai(self) -> bool:
        return self._client is not None

    # ==================== Vacancy Analysis ====================

    def analyzeVacancies(self, json_data: Dict[str, Any], branch_type: int) -> AnalysisResult:
        """
        Analyze vacancies JSON from hh.ru and extract skills.

        Args:
            json_data: JSON data from hh.ru API
            branch_type: 1 for position branch, 2 for skill branch

        Returns:
            AnalysisResult with position name and extracted skills

        Raises:
            ValueError: if json_data is empty or invalid
        """
        if not json_data:
            raise ValueError("Empty JSON data provided")

        items = json_data.get('items', [])
        if not items:
            raise ValueError("No vacancies found in JSON data")

        position_name = items[0].get('name', 'Unknown Position')

        if self._use_ai:
            try:
                skills = self._ai_analyze_vacancies(items, branch_type)
                return AnalysisResult(position_name=position_name, skills=skills)
            except Exception as e:
                print(f"[AIAssistant] AI analysis failed: {e}, falling back to mock")

        # Mock fallback
        mock_skills = self._extract_mock_skills(position_name)
        return AnalysisResult(position_name=position_name, skills=mock_skills)

    def _ai_analyze_vacancies(self, items: list, branch_type: int) -> List[Dict[str, Any]]:
        """Use OpenAI to extract skills from vacancy texts"""
        # Build a condensed text from vacancies
        vacancy_texts = []
        for item in items[:10]:
            name = item.get('name', '')
            snippet = item.get('snippet', {})
            requirement = snippet.get('requirement', '') or ''
            responsibility = snippet.get('responsibility', '') or ''
            vacancy_texts.append(f"Вакансия: {name}\nТребования: {requirement}\nОбязанности: {responsibility}")

        combined_text = "\n\n".join(vacancy_texts)

        prompt = f"""Проанализируй следующие вакансии с hh.ru и извлеки ключевые навыки.
Для каждого навыка укажи:
- name: название навыка с конкретным указанием что нужно
- frequency: частота встречаемости в вакансиях (0-100)
- importance: "important" если навык обязательный, "not_important" если желательный

Верни ТОЛЬКО JSON-массив навыков, без пояснений.
Пример: [{{"name": "Уметь работать с базами данных SQL", "frequency": 95, "importance": "important"}}]

Вакансии:
{combined_text}"""

        response = self._client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000
        )

        content = response.choices[0].message.content.strip()
        # Extract JSON from response (handle markdown code blocks)
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        skills = json.loads(content)
        if not isinstance(skills, list):
            raise ValueError("AI returned non-list response")

        # Validate and normalize
        for s in skills:
            if "frequency" not in s:
                s["frequency"] = 50
            if "importance" not in s or s["importance"] not in ["important", "not_important"]:
                s["importance"] = "important"

        return skills

    # ==================== Learning Plan Generation ====================

    def generateLearningPlan(self, deficit_skills: List[Dict[str, Any]],
                             level: str = "middle",
                             period: str = "6 месяцев",
                             time_per_day: str = "60") -> Dict[str, Any]:
        """
        Generate a personalized learning plan based on skill deficits.

        Args:
            deficit_skills: list of {"name", "frequency", "importance"}
            level: user level (junior/middle/senior)
            period: learning period
            time_per_day: minutes per day

        Returns:
            dict with "title" and "steps" (list of step dicts)
        """
        if self._use_ai:
            try:
                return self._ai_generate_plan(deficit_skills, level, period, time_per_day)
            except Exception as e:
                print(f"[AIAssistant] AI plan generation failed: {e}, falling back to mock")

        return self._mock_generate_plan(deficit_skills, level, period, time_per_day)

    def _ai_generate_plan(self, deficit_skills, level, period, time_per_day) -> Dict[str, Any]:
        """Use OpenAI to generate a learning plan"""
        skills_text = "\n".join(
            f"- {s['name']} (частота: {s.get('frequency', '?')}%, важность: {s.get('importance', '?')})"
            for s in deficit_skills
        )

        prompt = f"""Ты — карьерный консультант. Составь персонализированный пошаговый план обучения.

Уровень пользователя: {level}
Срок обучения: {period}
Время в день: {time_per_day} минут

Недостающие навыки:
{skills_text}

Для каждого шага укажи:
- skill: название навыка
- description: что именно изучать и в каком порядке (1-3 предложения)
- materials: массив из 1-3 бесплатных обучающих ресурсов. Каждый ресурс — объект с полями:
  - title: название ресурса
  - url: ссылка (предпочитай stepik.org, youtube.com, habr.com, coursera.org, w3schools.com, realpython.com, docs.python.org, ru.hexlet.io, kaggle.com, leetcode.com, geeksforgeeks.org)
  - type: "course"/"article"/"video"/"interactive"

Верни JSON-объект с полями "title" (название плана) и "steps" (массив шагов).
Без пояснений, только JSON."""

        response = self._client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=3000
        )

        content = response.choices[0].message.content.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        plan = json.loads(content)
        if "steps" not in plan:
            raise ValueError("AI response missing 'steps' field")
        if "title" not in plan:
            plan["title"] = "Персонализированный план обучения"

        return plan

    def _mock_generate_plan(self, deficit_skills, level, period, time_per_day) -> Dict[str, Any]:
        """Mock plan generation when AI is unavailable"""
        steps = []
        for i, skill in enumerate(deficit_skills, start=1):
            name = skill.get("name", f"Навык {i}")
            steps.append({
                "skill": name,
                "description": f"Изучите основы {name}. Рекомендуется начать с бесплатных курсов и практических заданий. Уделяйте {time_per_day} минут в день.",
                "materials": [
                    {"title": f"Курс по {name}", "url": f"https://stepik.org/catalog?search={name}", "type": "course"},
                    {"title": f"Статьи о {name}", "url": f"https://habr.com/ru/search/?q={name}", "type": "article"},
                ]
            })

        return {
            "title": f"План обучения ({level}, {period})",
            "steps": steps
        }

    # ==================== Analyze Skills (by-skill branch) ====================

    def analyzeBySkills(self, user_skills: List[str]) -> Dict[str, Any]:
        """
        Find matching professions based on user's skills.

        Args:
            user_skills: list of skill names the user has

        Returns:
            dict with "professions" list
        """
        if self._use_ai:
            try:
                return self._ai_analyze_by_skills(user_skills)
            except Exception as e:
                print(f"[AIAssistant] AI by-skills failed: {e}, falling back to mock")

        return self._mock_analyze_by_skills(user_skills)

    def _ai_analyze_by_skills(self, user_skills) -> Dict[str, Any]:
        """Use OpenAI to find matching professions"""
        skills_text = ", ".join(user_skills)

        prompt = f"""На основе навыков пользователя определи подходящие профессии.
Навыки пользователя: {skills_text}

Для каждой профессии укажи:
- name: название профессии
- match_percent: процент совпадения навыков (0-100)
- description: краткая рекомендация (1-2 предложения)
- missing_skills: массив недостающих навыков

Верни JSON-объект с полем "professions" (массив из 3-5 профессий).
Без пояснений, только JSON."""

        response = self._client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000
        )

        content = response.choices[0].message.content.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        result = json.loads(content)
        if "professions" not in result:
            raise ValueError("AI response missing 'professions' field")
        return result

    def _mock_analyze_by_skills(self, user_skills) -> Dict[str, Any]:
        """Mock profession matching"""
        professions = [
            {"name": "Python Developer", "match_percent": 75,
             "description": "Подходит для вашего набора навыков. Рекомендуется углубить знания в фреймворках.",
             "missing_skills": ["Django", "Docker"]},
            {"name": "Data Analyst", "match_percent": 60,
             "description": "Частичное совпадение. Необходимо изучить аналитические инструменты.",
             "missing_skills": ["Pandas", "Tableau"]},
            {"name": "Backend Developer", "match_percent": 50,
             "description": "Базовые навыки имеются, но нужны серверные технологии.",
             "missing_skills": ["REST API", "PostgreSQL"]},
        ]
        return {"professions": professions}

    # ==================== Mock Skills Fallback ====================

    def _extract_mock_skills(self, position_name: str) -> List[Dict[str, Any]]:
        """Mock skill extraction based on position name"""
        skills_map = {
            "python": [
                {"name": "Python", "frequency": 95, "importance": "important"},
                {"name": "SQL", "frequency": 85, "importance": "important"},
                {"name": "Git", "frequency": 80, "importance": "important"},
                {"name": "Django", "frequency": 70, "importance": "important"},
                {"name": "Docker", "frequency": 65, "importance": "not_important"},
            ],
            "data scientist": [
                {"name": "Python", "frequency": 95, "importance": "important"},
                {"name": "SQL", "frequency": 90, "importance": "important"},
                {"name": "Machine Learning", "frequency": 88, "importance": "important"},
                {"name": "Pandas", "frequency": 85, "importance": "important"},
                {"name": "Statistics", "frequency": 80, "importance": "important"},
            ],
            "java": [
                {"name": "Java", "frequency": 95, "importance": "important"},
                {"name": "Spring", "frequency": 85, "importance": "important"},
                {"name": "SQL", "frequency": 80, "importance": "important"},
                {"name": "Maven", "frequency": 75, "importance": "not_important"},
            ],
            "frontend": [
                {"name": "JavaScript", "frequency": 98, "importance": "important"},
                {"name": "CSS", "frequency": 92, "importance": "important"},
                {"name": "Vue.js", "frequency": 65, "importance": "important"},
                {"name": "React", "frequency": 70, "importance": "not_important"},
                {"name": "TypeScript", "frequency": 55, "importance": "not_important"},
            ],
        }

        lower_name = position_name.lower()
        for key, skills in skills_map.items():
            if key in lower_name:
                return skills

        return [
            {"name": "Programming", "frequency": 80, "importance": "important"},
            {"name": "Problem Solving", "frequency": 75, "importance": "important"},
            {"name": "Teamwork", "frequency": 70, "importance": "not_important"},
        ]