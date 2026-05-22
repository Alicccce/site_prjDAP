# -*- coding: utf-8 -*-
# tests/test_analyze_skills.py

import sys
import os
import pytest
import json
from collections import Counter
from unittest.mock import mock_open, patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend', 'hh_parser'))

# èìïîðòèðóåì ôóíêöèè èç analyze_skills.py
from analyze_skills import extract_skills, SKILLS, skills_lower


class TestExtractSkills:
    """tests for extract_skills function"""
    
    def test_extract_skills_single(self):
        """test: extract single skill from text"""
        text = "We need a Python developer with experience"
        skills = extract_skills(text)
        
        assert "Python" in skills
        assert len(skills) == 1
    
    def test_extract_skills_multiple(self):
        """test: extract multiple skills from text"""
        text = "Python, SQL and Docker are required"
        skills = extract_skills(text)
        
        assert "Python" in skills
        assert "SQL" in skills
        assert "Docker" in skills
    
    def test_extract_skills_case_insensitive(self):
        """test: skill extraction is case insensitive"""
        text = "PYTHON and sql expertise needed"
        skills = extract_skills(text)
        
        assert "Python" in skills
        assert "SQL" in skills
    
    def test_extract_skills_empty_text(self):
        """test: empty text returns empty list"""
        skills = extract_skills("")
        assert skills == []
    
    def test_extract_skills_none_text(self):
        """test: None text returns empty list"""
        skills = extract_skills(None)
        assert skills == []
    
    def test_extract_skills_skill_not_found(self):
        """test: skill not in dictionary returns empty"""
        text = "This text has no programming skills"
        skills = extract_skills(text)
        
        assert skills == []
    
    def test_extract_skills_duplicate_skills(self):
        """test: duplicate skills in text return unique list"""
        text = "Python and Python and more Python"
        skills = extract_skills(text)
        
        # should return unique skills
        assert len(skills) == 1
        assert skills[0] == "Python"


class TestSkillsDictionary:
    """tests for skills dictionary"""
    
    def test_skills_dictionary_has_common_skills(self):
        """test: skills dictionary contains common programming skills"""
        common_skills = ["Python", "Java", "SQL", "Docker", "Git", "PostgreSQL"]
        
        for skill in common_skills:
            assert skill in SKILLS, f"Skill '{skill}' not found in SKILLS"
    
    def test_skills_lower_has_correct_mapping(self):
        """test: skills_lower has correct case-insensitive mapping"""
        assert skills_lower["python"] == "Python"
        assert skills_lower["sql"] == "SQL"
        assert skills_lower["docker"] == "Docker"
    
    def test_skills_lower_contains_all_skills(self):
        """test: every skill in SKILLS has entry in skills_lower"""
        for skill in SKILLS:
            assert skill.lower() in skills_lower
            assert skills_lower[skill.lower()] == skill


class TestSkillFrequencyAnalysis:
    """tests for skill frequency analysis logic"""
    
    def test_skill_frequency_calculation(self):
        """test: frequency calculation works correctly"""
        # mock vacancies data
        vacancies = [
            {"name": "Python Developer", "snippet": {"requirement": "Python required"}},
            {"name": "Java Developer", "snippet": {"requirement": "Java required"}},
            {"name": "Full Stack", "snippet": {"requirement": "Python and Java"}},
        ]
        
        skill_counter = Counter()
        total_vacancies = len(vacancies)
        
        for vacancy in vacancies:
            text_parts = []
            if vacancy.get('name'):
                text_parts.append(vacancy['name'])
            snippet = vacancy.get('snippet', {})
            if snippet.get('requirement'):
                text_parts.append(snippet['requirement'])
            
            full_text = ' '.join(text_parts)
            skills = extract_skills(full_text)
            
            for skill in set(skills):
                skill_counter[skill] += 1
        
        # Python should appear in 2 vacancies: vacancy 1 and 3
        assert skill_counter.get("Python", 0) == 2
        # Java should appear in 2 vacancies: vacancy 2 and 3
        assert skill_counter.get("Java", 0) == 2
        
        # frequency for Python: 2/3 = 66.7%
        python_freq = (skill_counter.get("Python", 0) / total_vacancies) * 100
        assert 66 < python_freq < 67
    
    def test_skill_importance_classification(self):
        """test: importance classification based on frequency"""
        total = 10
        
        # mandatory: >70%
        assert self._get_importance(8, total) == "mandatory"  # 80%
        
        # recommended: >40% and <=70%
        assert self._get_importance(5, total) == "recommended"# 50%
        assert self._get_importance(7, total) == "recommended"# 70% (not >70%)
        
        # desirable: <=40%
        assert self._get_importance(4, total) == "desirable"# 40%
        assert self._get_importance(2, total) == "desirable"# 20%
    
    def _get_importance(self, count, total):
        """helper method for importance classification"""
        frequency = (count / total) * 100
        if frequency > 70:
            return "mandatory"
        elif frequency > 40:
            return "recommended"
        else:
            return "desirable"


class TestAnalyzeSkillsIntegration:
    """integration tests for analyze_skills.py workflow"""
    
    def test_analyze_with_sample_vacancies(self, tmp_path):
        """test: full analysis workflow with sample data"""
        # create sample vacancies.json
        sample_vacancies = {
            "items": [
                {
                    "name": "Python Developer",
                    "snippet": {"requirement": "Python, SQL, Docker"}
                },
                {
                    "name": "Data Scientist",
                    "snippet": {"requirement": "Python, Machine Learning, SQL"}
                },
                {
                    "name": "Java Developer",
                    "snippet": {"requirement": "Java, Spring, SQL"}
                }
            ],
            "found": 3
        }
        
        vacancies_file = tmp_path / "vacancies.json"
        with open(vacancies_file, 'w', encoding='utf-8') as f:
            json.dump(sample_vacancies, f)
        
        # read and analyze
        with open(vacancies_file, 'r', encoding='utf-8') as f:
            vacancies_data = json.load(f)
        
        vacancies = vacancies_data.get('items', [])
        skill_counter = Counter()
        total_vacancies = len(vacancies)
        
        for vacancy in vacancies:
            text_parts = []
            if vacancy.get('name'):
                text_parts.append(vacancy['name'])
            snippet = vacancy.get('snippet', {})
            if snippet.get('requirement'):
                text_parts.append(snippet['requirement'])
            
            full_text = ' '.join(text_parts)
            skills = extract_skills(full_text)
            
            for skill in set(skills):
                skill_counter[skill] += 1
        
        # verify results
        assert total_vacancies == 3
        assert skill_counter.get("Python", 0) == 2# Python Developer + Data Scientist
        assert skill_counter.get("SQL", 0) == 3# all 3 vacancies
        assert skill_counter.get("Docker", 0) == 1# only Python Developer
        
        # SQL should be mandatory (100% frequency)
        sql_freq = (skill_counter.get("SQL", 0) / total_vacancies) * 100
        assert sql_freq == 100
        
        # Docker should be rare
        docker_freq = (skill_counter.get("Docker", 0) / total_vacancies) * 100
        assert docker_freq < 40


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
