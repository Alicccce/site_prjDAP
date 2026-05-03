# -*- coding: utf-8 -*-
# tests/test_hh_client.py

import sys
import os
import pytest
import requests
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hh_client import HHClient, load_token_from_file


class TestLoadTokenFromFile:
    """tests for load_token_from_file function"""
    
    def test_load_token_success(self, tmp_path):
        token_file = tmp_path / "token.txt"
        token_file.write_text("test_access_token_123")
        
        with patch('hh_client.TOKEN_FILE', str(token_file)):
            token = load_token_from_file()
            assert token == "test_access_token_123"
    
    def test_load_token_with_whitespace(self, tmp_path):
        token_file = tmp_path / "token.txt"
        token_file.write_text("  my_token_456\n  ")
        
        with patch('hh_client.TOKEN_FILE', str(token_file)):
            token = load_token_from_file()
            assert token == "my_token_456"
    
    def test_load_token_file_not_found(self):
        with patch('hh_client.TOKEN_FILE', 'non_existent_file.txt'):
            token = load_token_from_file()
            assert token is None
    
    def test_load_token_empty_file(self, tmp_path):
        token_file = tmp_path / "token.txt"
        token_file.write_text("")
        
        with patch('hh_client.TOKEN_FILE', str(token_file)):
            token = load_token_from_file()
            assert token == ""


class TestHHClientInit:
    """tests for HHClient initialization"""
    
    def test_init_with_explicit_token(self):
        client = HHClient(token="explicit_token")
        assert client.token == "explicit_token"
        assert client.base_url == "https://api.hh.ru/vacancies"
        assert client.per_page == 20
    
    def test_init_without_token_loads_from_file(self):
        with patch('hh_client.load_token_from_file', return_value="file_token"):
            client = HHClient()
            assert client.token == "file_token"
    
    def test_init_without_token_file_not_found(self):
        with patch('hh_client.load_token_from_file', return_value=None):
            client = HHClient()
            assert client.token is None


class TestGetHeaders:
    """tests for _get_headers method"""
    
    def test_headers_without_token(self):
        """test: headers without token"""
        # отключаем загрузку токена и передаём None в явном виде
        with patch('hh_client.load_token_from_file', return_value=None):
            client = HHClient(token=None)
            headers = client._get_headers()
            
            assert "User-Agent" in headers
            assert "Authorization" not in headers
    
    def test_headers_with_token(self):
        client = HHClient(token="my_secret_token")
        headers = client._get_headers()
        
        assert "User-Agent" in headers
        assert headers["Authorization"] == "Bearer my_secret_token"
    
    def test_user_agent_is_random(self):
        with patch('hh_client.load_token_from_file', return_value=None):
            client = HHClient(token=None)
            headers = client._get_headers()
            
            assert headers["User-Agent"] in [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            ]


class TestFetchVacancies:
    """tests for fetch_vacancies method"""
    
    def test_fetch_vacancies_success(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'found': 10,
            'items': [
                {'name': 'Python Developer', 'employer': {'name': 'Test Corp'}}
            ]
        }
        
        with patch('requests.get', return_value=mock_response):
            client = HHClient(token="test_token")
            result = client.fetch_vacancies("Python Developer")
            
            assert result['found'] == 10
    
    def test_fetch_vacancies_no_results(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'found': 0, 'items': []}
        
        with patch('requests.get', return_value=mock_response):
            client = HHClient(token="test_token")
            
            with pytest.raises(ValueError, match="No vacancies found"):
                client.fetch_vacancies("Nonexistent Position")
    
    def test_fetch_vacancies_status_code_error(self):
        mock_response = Mock()
        mock_response.status_code = 403
        
        with patch('requests.get', return_value=mock_response):
            client = HHClient(token="test_token")
            
            with pytest.raises(ConnectionError, match="hh.ru returned status code 403"):
                client.fetch_vacancies("Python")
    
    def test_fetch_vacancies_timeout(self):
        with patch('requests.get', side_effect=requests.exceptions.Timeout()):
            client = HHClient(token="test_token")
            
            with pytest.raises(TimeoutError, match="hh.ru is not responding"):
                client.fetch_vacancies("Python")
    
    def test_fetch_vacancies_connection_error(self):
        with patch('requests.get', side_effect=requests.exceptions.ConnectionError()):
            client = HHClient(token="test_token")
            
            with pytest.raises(ConnectionError, match="No connection to hh.ru"):
                client.fetch_vacancies("Python")


class TestGetVacanciesCount:
    """tests for get_vacancies_count method"""
    
    def test_get_vacancies_count_success(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'found': 42, 'items': []}
        
        with patch('requests.get', return_value=mock_response):
            client = HHClient(token="test_token")
            count = client.get_vacancies_count("Python Developer")
            
            assert count == 42
    
    def test_get_vacancies_count_zero_on_error(self):
        """test: returns 0 on error (should NOT raise exception)"""
        with patch('requests.get', side_effect=requests.exceptions.Timeout()):
            client = HHClient(token="test_token")
            count = client.get_vacancies_count("Python Developer")
            
            # метод должен вернуть 0, а не бросить исключение
            assert count == 0


class TestGetVacanciesList:
    """tests for get_vacancies_list method"""
    
    def test_get_vacancies_list_success(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'found': 10,
            'items': [
                {
                    'name': 'Python Developer',
                    'employer': {'name': 'Company A'},
                    'snippet': {'requirement': 'Python 3', 'responsibility': 'Write code'},
                    'alternate_url': 'https://hh.ru/vacancy/1'
                }
            ]
        }
        
        with patch('requests.get', return_value=mock_response):
            client = HHClient(token="test_token")
            vacancies = client.get_vacancies_list("Developer", limit=2)
            
            assert len(vacancies) == 1
            assert vacancies[0]['name'] == 'Python Developer'
    
    def test_get_vacancies_list_with_limit(self):
        mock_items = [{'name': f'Skill {i}'} for i in range(10)]
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'found': 100, 'items': mock_items}
        
        with patch('requests.get', return_value=mock_response):
            client = HHClient(token="test_token")
            vacancies = client.get_vacancies_list("Developer", limit=3)
            
            assert len(vacancies) == 3
    
    def test_get_vacancies_list_empty_on_error(self):
        """test: returns empty list on error (should NOT raise exception)"""
        with patch('requests.get', side_effect=requests.exceptions.Timeout()):
            client = HHClient(token="test_token")
            vacancies = client.get_vacancies_list("Developer")
            
            # метод должен вернуть пустой список, а не бросить исключение
            assert vacancies == []


class TestSaveToFile:
    """tests for save_to_file method"""
    
    def test_save_to_file_creates_json(self, tmp_path):
        """test: save_to_file creates JSON file"""
        data = {'found': 5, 'items': [{'name': 'Python Developer'}]}
        filename = tmp_path / "test_vacancies.json"
        
        client = HHClient(token="test_token")
        client.save_to_file(data, str(filename))
        
        assert filename.exists()
        
        import json
        with open(filename, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        assert loaded['found'] == 5
    
    def test_fetch_and_save(self, tmp_path):
        """test: fetch_and_save combines fetch and save"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'found': 3, 'items': [{'name': 'Test'}]}
        
        filename = tmp_path / "combined.json"
        
        with patch('requests.get', return_value=mock_response):
            client = HHClient(token="test_token")
            result = client.fetch_and_save("Test", str(filename))
            
            assert result is not None
            assert result['found'] == 3
            assert filename.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])