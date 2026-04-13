# -*- coding: utf-8 -*-
# services/ai_assistant.py
import colorama
from colorama import init, Fore, Style
# Инициализация colorama (автоматически настраивает кодировку)
init(autoreset=True)
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class AnalysisResult:
    """Result of AI vacancy analysis"""
    position_name: str
    skills: List[Dict[str, Any]]  # each skill: {"name": str, "frequency": int, "importance": str}


class AIAssistant:
    """
    AI Assistant for analyzing vacancies
    Currently a mock implementation - will be replaced with real AI later
    """
    
    def analyzeVacancies(self, json_data: Dict[str, Any], branch_type: int) -> AnalysisResult:
        """
        Analyze vacancies JSON from hh.ru and extract skills
        
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
        
        # mock implementation: extract position name from first vacancy
        first_vacancy = items[0]
        position_name = first_vacancy.get('name', 'Unknown Position')
        
        # mock skills extraction
        # in real implementation, AI would analyze requirements and responsibilities
        mock_skills = self._extract_mock_skills(position_name)
        
        return AnalysisResult(
            position_name=position_name,
            skills=mock_skills
        )
    
    def _extract_mock_skills(self, position_name: str) -> List[Dict[str, Any]]:
        """
        Mock skill extraction based on position name
        In real implementation, this would use NLP/AI
        """
        # common skills mapping for different positions
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
        }
        
        # find matching skills
        lower_name = position_name.lower()
        for key, skills in skills_map.items():
            if key in lower_name:
                return skills
        
        # default skills if no match
        return [
            {"name": "Programming", "frequency": 80, "importance": "important"},
            {"name": "Problem Solving", "frequency": 75, "importance": "important"},
            {"name": "Teamwork", "frequency": 70, "importance": "not_important"},
        ]