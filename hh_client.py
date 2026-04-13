# -*- coding: utf-8 -*-
# hh_client.py
import colorama
from colorama import init, Fore, Style
# Инициализация colorama (автоматически настраивает кодировку)
init(autoreset=True)
import requests
import random
from typing import Optional, Dict, Any, List

# Список User-Agent для ротации
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15",
]

class HHClient:
    """Client for fetching vacancies from hh.ru API"""
    
    def __init__(self):
        self.base_url = "https://api.hh.ru/vacancies"
        self.per_page = 20  # количество вакансий для анализа
    
    def fetch_vacancies(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Fetch vacancies from hh.ru by query
        
        Args:
            query: search query (e.g., "Data Scientist")
        
        Returns:
            JSON data from hh.ru or None if error
        
        Raises:
            TimeoutError: if hh.ru doesn't respond
            ConnectionError: if no connection
            ValueError: if empty result
        """
        # формируем URL с параметрами
        url = f"{self.base_url}?text={query}&per_page={self.per_page}"
        
        # случайный User-Agent
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        
        try:
            # отправляем GET-запрос
            response = requests.get(url, headers=headers, timeout=10)
            
            # проверяем, что ответ успешный
            if response.status_code == 200:
                data = response.json()
                
                # проверяем, есть ли результаты
                if data.get('found', 0) == 0:
                    raise ValueError(f"No vacancies found for query '{query}'")
                
                return data
            else:
                raise ConnectionError(f"hh.ru returned status code {response.status_code}")
                
        except requests.exceptions.Timeout:
            raise TimeoutError("hh.ru is not responding (timeout)")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("No connection to hh.ru")
        except Exception as e:
            raise  # пробрасываем исходное исключение
    
    def get_vacancies_count(self, query: str) -> int:
        """Get total number of vacancies for query"""
        data = self.fetch_vacancies(query)
        return data.get('found', 0) if data else 0
    
    def get_vacancies_list(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Get list of vacancies with basic info
        
        Args:
            query: search query
            limit: max number of vacancies to return
        
        Returns:
            list of dicts with vacancy info
        """
        data = self.fetch_vacancies(query)
        if not data:
            return []
        
        items = data.get('items', [])[:limit]
        vacancies = []
        
        for item in items:
            vacancies.append({
                'name': item.get('name'),
                'employer': item.get('employer', {}).get('name'),
                'requirement': item.get('snippet', {}).get('requirement', ''),
                'responsibility': item.get('snippet', {}).get('responsibility', ''),
                'url': item.get('alternate_url')
            })
        
        return vacancies


if __name__ == "__main__":
    # просто проверка, что модуль импортируется
    print("HHClient module ready for import")