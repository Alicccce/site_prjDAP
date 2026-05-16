# -*- coding: utf-8 -*-
# tests/test_vacancy_analysis_service.py
import colorama
from colorama import init, Fore, Style
init(autoreset=True)
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from sqlalchemy import create_engine
from DataBase import Base, User
from repositories.user_repo import UserRepository


def setup_test_db():
    """create temporary in-memory database for tests"""
    test_engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(test_engine)
    
    import DataBase as db_module
    original_engine = db_module.engine
    db_module.engine = test_engine
    
    return test_engine, original_engine


def cleanup_test_db(original_engine):
    """restore original engine"""
    import DataBase as db_module
    db_module.engine = original_engine


def create_test_user():
    """create a test user and return user object"""
    user_repo = UserRepository()
    
    # use unique email for each test
    import time
    unique_email = f"test_service_{int(time.time()*1000)}@example.com"
    
    test_user = User(
        email=unique_email,
        name="Service Test User",
        password_hash="test_hash_123"
    )
    created = user_repo.create(test_user)
    return created


class TestVacancyAnalysisService:
    """Test suite for VacancyAnalysisService"""
    
    def setup_method(self):
        """setup before each test"""
        self.test_engine, self.original_engine = setup_test_db()
        self.test_user = create_test_user()
    
    def teardown_method(self):
        """cleanup after each test"""
        cleanup_test_db(self.original_engine)
    
    def test_analyze_by_position_success(self):
        """test 1: successful position analysis"""
        
        # create mocks
        mock_hh = Mock()
        mock_hh.fetch_vacancies.return_value = {
            'found': 10,
            'items': [{'name': 'Python Developer', 'employer': {'name': 'Test Corp'}}]
        }
        
        mock_ai = Mock()
        mock_ai.analyzeVacancies.return_value = Mock(
            position_name='Python Developer',
            skills=[
                {'name': 'Python', 'frequency': 95, 'importance': 'important'},
                {'name': 'SQL', 'frequency': 85, 'importance': 'important'},
                {'name': 'Git', 'frequency': 80, 'importance': 'not_important'}
            ]
        )
        
        # patch at the module level where the service imports them
        with patch('services.vacancy_analysis_service.HHClient', return_value=mock_hh):
            with patch('services.vacancy_analysis_service.AIAssistant', return_value=mock_ai):
                from services.vacancy_analysis_service import VacancyAnalysisService
                service = VacancyAnalysisService()
                
                # call service
                result = service.analyzeByPosition(
                    user_id=self.test_user.id,
                    position_query="Python Developer"
                )
                
                # verify result
                assert len(result) == 3
                assert result[0]['skill_name'] == 'Python'
                assert result[0]['frequency'] == 95
                
                # verify session was created
                sessions = service.session_repo.find_by_user(self.test_user.id)
                assert len(sessions) == 1
                assert sessions[0].search_query == "Python Developer"
                
                print("Test_analyze_by_position_success passed")
    
    def test_analyze_by_position_empty_query(self):
        """test 2: empty query should raise error"""
        
        with patch('services.vacancy_analysis_service.HHClient'):
            with patch('services.vacancy_analysis_service.AIAssistant'):
                from services.vacancy_analysis_service import VacancyAnalysisService
                service = VacancyAnalysisService()
                
                with pytest.raises(ValueError, match="Position query cannot be empty"):
                    service.analyzeByPosition(
                        user_id=self.test_user.id,
                        position_query=""
                    )
                
                print("Test_analyze_by_position_empty_query passed")
    
    def test_analyze_by_position_no_vacancies(self):
        """test 3: no vacancies found"""
        
        mock_hh = Mock()
        mock_hh.fetch_vacancies.side_effect = ValueError("No vacancies found for query 'Nonexistent Position'")
        
        with patch('services.vacancy_analysis_service.HHClient', return_value=mock_hh):
            with patch('services.vacancy_analysis_service.AIAssistant'):
                from services.vacancy_analysis_service import VacancyAnalysisService
                service = VacancyAnalysisService()
                
                with pytest.raises(ValueError, match="No vacancies found"):
                    service.analyzeByPosition(
                        user_id=self.test_user.id,
                        position_query="Nonexistent Position"
                    )
                
                print("Test_analyze_by_position_no_vacancies passed")
    
    def test_analyze_by_position_ai_empty_result(self):
        """test 4: AI returns empty skills list"""
        
        mock_hh = Mock()
        mock_hh.fetch_vacancies.return_value = {
            'found': 5,
            'items': [{'name': 'Test Position'}]
        }
        
        mock_ai = Mock()
        mock_ai.analyzeVacancies.return_value = Mock(
            position_name='Test Position',
            skills=[]
        )
        
        with patch('services.vacancy_analysis_service.HHClient', return_value=mock_hh):
            with patch('services.vacancy_analysis_service.AIAssistant', return_value=mock_ai):
                from services.vacancy_analysis_service import VacancyAnalysisService
                service = VacancyAnalysisService()
                
                with pytest.raises(RuntimeError, match="AI returned empty skills list"):
                    service.analyzeByPosition(
                        user_id=self.test_user.id,
                        position_query="Test Position"
                    )
                
                print("Test_analyze_by_position_ai_empty_result passed")
    
    def test_duplicate_analysis_creates_new_session(self):
        """test 5: duplicate query creates new session (not overwrite)"""
        
        mock_hh = Mock()
        mock_hh.fetch_vacancies.return_value = {'found': 5, 'items': [{'name': 'Data Scientist'}]}
        
        mock_ai = Mock()
        mock_ai.analyzeVacancies.return_value = Mock(
            position_name='Data Scientist',
            skills=[{'name': 'Python', 'frequency': 90, 'importance': 'important'}]
        )
        
        with patch('services.vacancy_analysis_service.HHClient', return_value=mock_hh):
            with patch('services.vacancy_analysis_service.AIAssistant', return_value=mock_ai):
                from services.vacancy_analysis_service import VacancyAnalysisService
                service = VacancyAnalysisService()
                
                # first analysis
                service.analyzeByPosition(
                    user_id=self.test_user.id,
                    position_query="Data Scientist"
                )
                
                # second analysis with same query
                service.analyzeByPosition(
                    user_id=self.test_user.id,
                    position_query="Data Scientist"
                )
                
                # verify two sessions were created
                sessions = service.session_repo.find_by_user(self.test_user.id)
                assert len(sessions) == 2
                assert sessions[0].id != sessions[1].id
                
                print("Test_duplicate_analysis_creates_new_session passed")
    
    def test_analyze_by_position_frequency_validation(self):
        """test 6: frequency values are validated (0-100 range)"""
        
        mock_hh = Mock()
        mock_hh.fetch_vacancies.return_value = {'found': 5, 'items': [{'name': 'Test'}]}
        
        mock_ai = Mock()
        mock_ai.analyzeVacancies.return_value = Mock(
            position_name='Test Position',
            skills=[
                {'name': 'Skill1', 'frequency': 150, 'importance': 'important'},
                {'name': 'Skill2', 'frequency': -10, 'importance': 'important'},
                {'name': 'Skill3', 'frequency': 75, 'importance': 'important'}
            ]
        )
        
        with patch('services.vacancy_analysis_service.HHClient', return_value=mock_hh):
            with patch('services.vacancy_analysis_service.AIAssistant', return_value=mock_ai):
                from services.vacancy_analysis_service import VacancyAnalysisService
                service = VacancyAnalysisService()
                
                result = service.analyzeByPosition(
                    user_id=self.test_user.id,
                    position_query="Test"
                )
                
                # find skills by name
                skill1 = next((s for s in result if s['skill_name'] == 'Skill1'), None)
                skill2 = next((s for s in result if s['skill_name'] == 'Skill2'), None)
                skill3 = next((s for s in result if s['skill_name'] == 'Skill3'), None)
                
                assert skill1 is not None
                assert skill2 is not None
                assert skill3 is not None
                assert skill1['frequency'] == 100
                assert skill2['frequency'] == 0
                assert skill3['frequency'] == 75
                
                print("Test_analyze_by_position_frequency_validation passed")
    
    def test_get_user_position_history(self):
        """test 7: get user position history"""
        
        mock_hh = Mock()
        mock_hh.fetch_vacancies.return_value = {'found': 5, 'items': [{'name': 'Test'}]}
        
        mock_ai = Mock()
        mock_ai.analyzeVacancies.return_value = Mock(
            position_name='Test Position',
            skills=[{'name': 'Python', 'frequency': 90, 'importance': 'important'}]
        )
        
        with patch('services.vacancy_analysis_service.HHClient', return_value=mock_hh):
            with patch('services.vacancy_analysis_service.AIAssistant', return_value=mock_ai):
                from services.vacancy_analysis_service import VacancyAnalysisService
                service = VacancyAnalysisService()
                
                # run two analyses
                service.analyzeByPosition(self.test_user.id, "Python Developer")
                service.analyzeByPosition(self.test_user.id, "Data Scientist")
                
                # get history
                history = service.get_user_position_history(self.test_user.id)
                
                assert len(history) == 2
                
                print("Test_get_user_position_history passed")


if __name__ == "__main__":
    print("Run with: pytest tests/test_vacancy_analysis_service.py -v")
