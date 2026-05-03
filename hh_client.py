# -*- coding: utf-8 -*-
# hh_client.py
import requests
import random
import os
import json
from typing import Optional, Dict, Any, List
from pathlib import Path

# list of User-Agent for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]

TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "token.txt")
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hh_cache")
CLIENT_ID = "R91SLJTUU2ICK85ASGB421VHH716I6G5IODTUK7RA6AFRPH8EGA41KJDMED70VHA"
CLIENT_SECRET = "J9R1GESPB1VTGRUIIV0OFG38COL5FJO3N23MUR7AO1KCK8LVVDR18F4UP7UMPQQO"


def load_token_from_file() -> Optional[str]:
    """loads token from token.txt file"""
    try:
        with open(TOKEN_FILE, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def refresh_token() -> Optional[str]:
    """Gets a new token via client_credentials and saves it to token.txt"""
    try:
        print("  [HHClient] refreshing token via client_credentials...")
        r = requests.post("https://hh.ru/oauth/token", data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        }, timeout=10)
        if r.status_code == 200:
            new_token = r.json().get("access_token")
            if new_token:
                with open(TOKEN_FILE, 'w') as f:
                    f.write(new_token)
                print(f"  [HHClient] new token saved: {new_token[:10]}...")
                return new_token
        print(f"  [HHClient] token refresh failed: {r.status_code} {r.text[:100]}")
    except Exception as e:
        print(f"  [HHClient] token refresh error: {e}")
    return None


class HHClient:
    """Client for fetching vacancies from hh.ru API with OAuth token support and caching fallback"""
    
    def __init__(self, token: Optional[str] = None):
        self.base_url = "https://api.hh.ru/vacancies"
        self.per_page = 50  # increased for better skill frequency accuracy
        
        if token:
            self.token = token
        else:
            self.token = load_token_from_file()

        # Ensure cache directory exists
        os.makedirs(CACHE_DIR, exist_ok=True)
    
    def _get_headers(self) -> Dict[str, str]:
        """creates headers for request (with or without token)"""
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def _cache_path(self, query: str) -> str:
        """Get cache file path for a query"""
        safe_name = query.replace(' ', '_').replace('/', '_')[:50]
        return os.path.join(CACHE_DIR, f"cache_{safe_name}.json")

    def _enrich_with_key_skills(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetches detail page for each vacancy to get key_skills.
        Adds 'key_skills' list to each item in-place.
        Skips vacancies that fail (timeout/error) — they just get empty key_skills.
        """
        items = data.get('items', [])
        print(f"  [HHClient] fetching key_skills for {len(items)} vacancies...")
        enriched = 0
        for item in items:
            vid = item.get('id')
            if not vid:
                item.setdefault('key_skills', [])
                continue
            try:
                r = requests.get(
                    f"https://api.hh.ru/vacancies/{vid}",
                    headers=self._get_headers(),
                    timeout=5
                )
                if r.status_code == 200:
                    detail = r.json()
                    item['key_skills'] = detail.get('key_skills', [])
                    if item['key_skills']:
                        enriched += 1
                else:
                    item.setdefault('key_skills', [])
            except Exception:
                item.setdefault('key_skills', [])
        print(f"  [HHClient] {enriched}/{len(items)} vacancies have key_skills")
        return data

    def _save_to_cache(self, query: str, data: Dict[str, Any]) -> None:
        """Save successful response to cache file"""
        try:
            cache_file = self._cache_path(query)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"  [HHClient] cached response for '{query}'")
        except Exception as e:
            print(f"  [HHClient] cache write failed: {e}")

    def _load_from_cache(self, query: str) -> Optional[Dict[str, Any]]:
        """Load last successful response from cache (fallback when HH.ru is unavailable)"""
        try:
            cache_file = self._cache_path(query)
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"  [HHClient] loaded cached response for '{query}'")
                return data
        except Exception as e:
            print(f"  [HHClient] cache read failed: {e}")
        return None

    def fetch_vacancies(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Fetch vacancies from hh.ru by query with key_skills from detail pages.
        Falls back to cache on failure.
        """
        url = f"{self.base_url}?text={query}&per_page={self.per_page}"
        
        print(f"  [HHClient] using token: {'YES' if self.token else 'NO'}")

        try:
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('found', 0) == 0:
                    raise ValueError(f"No vacancies found for query '{query}'")
                
                # Enrich each vacancy with key_skills from detail page
                data = self._enrich_with_key_skills(data)
                
                # Save successful response to cache
                self._save_to_cache(query, data)
                return data
            elif response.status_code == 403:
                # Token revoked or blocked — try to refresh token first
                print(f"  [HHClient] got 403, attempting token refresh...")
                new_token = refresh_token()
                if new_token:
                    self.token = new_token
                    # Retry once with new token
                    retry = requests.get(url, headers=self._get_headers(), timeout=10)
                    if retry.status_code == 200:
                        data = retry.json()
                        data = self._enrich_with_key_skills(data)
                        self._save_to_cache(query, data)
                        return data
                # Fall back to cache
                print(f"  [HHClient] token refresh failed, trying cache...")
                cached = self._load_from_cache(query)
                if cached:
                    return cached
                raise ConnectionError(f"hh.ru blocked request and no cache available for '{query}'")
            else:
                raise ConnectionError(f"hh.ru returned status code {response.status_code}")
                
        except (requests.exceptions.Timeout, TimeoutError):
            print(f"  [HHClient] timeout, trying cache...")
            cached = self._load_from_cache(query)
            if cached:
                return cached
            raise TimeoutError("hh.ru is not responding (timeout) and no cache available")
        except requests.exceptions.ConnectionError:
            print(f"  [HHClient] connection error, trying cache...")
            cached = self._load_from_cache(query)
            if cached:
                return cached
            raise ConnectionError("No connection to hh.ru and no cache available")
        except ValueError:
            raise
        except Exception as e:
            cached = self._load_from_cache(query)
            if cached:
                return cached
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