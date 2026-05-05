# -*- coding: utf-8 -*-
# services/position_suggest_service.py
"""
Service for branch 2: "Don't know what I want".
Accepts user filters and dialog skill answers,
then parses HH.ru and returns top-3 matching positions.
"""

from typing import List, Dict, Any, Optional
from hh_client import HHClient
from services.skill_extractor import extract_skills_from_vacancies


SPECIALIZATION_QUERIES = {
    "Frontend-разработчик": ["Frontend разработчик", "Vue разработчик", "React разработчик"],
    "Backend-разработчик": ["Backend разработчик", "Python разработчик", "Java разработчик"],
    "Data Scientist": ["Data Scientist", "ML инженер", "Аналитик данных"],
    "DevOps-инженер": ["DevOps инженер", "SRE инженер", "Системный администратор"],
    "QA-инженер": ["QA инженер", "Тестировщик", "Automation QA"],
    "UX/UI-дизайнер": ["UX дизайнер", "UI дизайнер", "Product дизайнер"],
    "Аналитик": ["Бизнес аналитик", "Системный аналитик", "Продуктовый аналитик"],
    "Продуктовый менеджер": ["Product Manager", "Продуктовый менеджер", "Project Manager"],
}

DEFAULT_QUERIES = [
    "Python разработчик",
    "Frontend разработчик",
    "Data Scientist",
    "DevOps инженер",
    "Аналитик данных",
]

INDUSTRY_KEYWORDS = {
    "Информационные технологии": "IT",
    "Финансы и банки": "банк финтех",
    "Ритейл": "ритейл e-commerce",
    "Маркетинг и реклама": "маркетинг",
    "Образование": "edtech образование",
    "Медицина": "медтех healthtech",
    "Производство": "производство",
}


class PositionSuggestService:

    def __init__(self):
        self.hh_client = HHClient()

    def suggest_positions(
        self,
        filters: Dict[str, Any],
        user_skills: List[str],
        max_positions: int = 3
    ) -> List[Dict[str, Any]]:
        queries = self._build_queries(filters)
        results = []
        seen_titles = set()

        for query in queries:
            try:
                print(f"[PositionSuggest] Fetching '{query}'...")
                vacancies_data = self.hh_client.fetch_vacancies_fast(query)
                if not vacancies_data:
                    continue

                skills = extract_skills_from_vacancies(vacancies_data, top_n=20)
                if not skills:
                    continue

                title = self._normalize_title(query, filters.get("industry", ""))
                if title in seen_titles:
                    continue
                seen_titles.add(title)

                total_vacancies = vacancies_data.get("found", 0)
                position_skill_names = [s["name"] for s in skills]
                match_skills, new_skills = self._match_skills(user_skills, position_skill_names)
                mandatory_skills = [s["name"] for s in skills if s["importance"] == "important"]
                match_score = self._calc_match_score(user_skills, mandatory_skills)

                results.append({
                    "title": title,
                    "query": query,
                    "match_skills": match_skills,
                    "new_skills": new_skills[:3],
                    "all_skills": skills,
                    "total_vacancies": total_vacancies,
                    "match_score": match_score,
                })

            except Exception as e:
                print(f"[PositionSuggest] Error for '{query}': {e}")
                continue

        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results[:max_positions]

    def _build_queries(self, filters: Dict[str, Any]) -> List[str]:
        specialization = filters.get("specialization", "")
        industry = filters.get("industry", "")

        if specialization and specialization in SPECIALIZATION_QUERIES:
            queries = SPECIALIZATION_QUERIES[specialization].copy()
        else:
            queries = DEFAULT_QUERIES.copy()

        if industry and industry in INDUSTRY_KEYWORDS:
            kw = INDUSTRY_KEYWORDS[industry]
            queries = [f"{q} {kw}" for q in queries[:2]] + queries[2:]

        return queries[:3]  # limit to 3 queries for speed

    def _normalize_title(self, query: str, industry: str) -> str:
        if industry and industry in INDUSTRY_KEYWORDS:
            kw = INDUSTRY_KEYWORDS[industry]
            query = query.replace(f" {kw}", "").strip()
        return query

    def _match_skills(
        self, user_skills: List[str], position_skills: List[str]
    ):
        user_lower = {s.lower().strip() for s in user_skills}
        match, new = [], []
        for skill in position_skills:
            if skill.lower().strip() in user_lower:
                match.append(skill)
            else:
                new.append(skill)
        return match, new

    def _calc_match_score(self, user_skills: List[str], mandatory_skills: List[str]) -> int:
        if not mandatory_skills:
            return 0
        user_lower = {s.lower().strip() for s in user_skills}
        matched = sum(1 for s in mandatory_skills if s.lower().strip() in user_lower)
        return round((matched / len(mandatory_skills)) * 100)
