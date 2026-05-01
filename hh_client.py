# -*- coding: utf-8 -*-
# hh_client.py
import requests
import random
import os
import json
from typing import Optional, Dict, Any, List

# list of User-Agent for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
]

TOKEN_FILE = "token.txt"


def load_token_from_file() -> Optional[str]:
    """loads token from token.txt file"""
    try:
        with open(TOKEN_FILE, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


class HHClient:
    """Client for fetching vacancies from hh.ru API with OAuth token support"""
    
    def __init__(self, token: Optional[str] = None):
        self.base_url = "https://api.hh.ru/vacancies"
        self.per_page = 20
        
        if token:
            self.token = token
        else:
            self.token = load_token_from_file()
    
    def _get_headers(self) -> Dict[str, str]:
        """creates headers for request (with or without token)"""
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def fetch_vacancies(self, query: str) -> Optional[Dict[str, Any]]:
        """Fetch vacancies from hh.ru by query"""
        url = f"{self.base_url}?text={query}&per_page={self.per_page}"
        
        print(f"  [HHClient] using token: {'YES' if self.token else 'NO'}")

        try:
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
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
            raise
    
    def get_vacancies_count(self, query: str) -> int:
        """Get total number of vacancies for query (returns 0 on error)"""
        try:
            data = self.fetch_vacancies(query)
            return data.get('found', 0) if data else 0
        except Exception:
            return 0
    
    def get_vacancies_list(self, query: str, limit: int = 10) -> List[Dict]:
        """Get list of vacancies with basic info (returns empty list on error)"""
        try:
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
        except Exception:
            return []
    
    def save_to_file(self, data: Dict[str, Any], filename: str = "vacancies.json") -> None:
        """
        Save vacancies data to JSON file
        
        Args:
            data: JSON data from fetch_vacancies
            filename: output file name (default: vacancies.json)
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  [HHClient] saved {len(data.get('items', []))} vacancies to {filename}")
    
    def fetch_and_save(self, query: str, filename: str = "vacancies.json") -> Optional[Dict[str, Any]]:
        """
        Fetch vacancies and save to JSON file in one call
        
        Args:
            query: search query
            filename: output file name
        
        Returns:
            JSON data from hh.ru
        """
        data = self.fetch_vacancies(query)
        if data:
            self.save_to_file(data, filename)
        return data


if __name__ == "__main__":
    print("HHClient module ready for import")