# database.py
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class Database:
    def __init__(self, db_path: str = "vacancies.db"):
        self.db_path = db_path
        self._init_tables()

    def _init_tables(self):
        """Создание всех необходимых таблиц"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Таблица для кэширования результатов поиска
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    search_query TEXT NOT NULL,
                    area INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    vacancies_count INTEGER,
                    analysis_result TEXT NOT NULL,
                    UNIQUE(search_query, area)
                )
            """)

            # Таблица для хранения анализов навыков
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS skills_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    search_query TEXT NOT NULL,
                    job_title TEXT,
                    skill_name TEXT NOT NULL,
                    frequency REAL NOT NULL,
                    importance TEXT NOT NULL,
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Таблица для метрик и логов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    search_query TEXT NOT NULL,
                    parse_time_seconds REAL,
                    analysis_time_seconds REAL,
                    vacancies_processed INTEGER,
                    skills_found INTEGER,
                    cache_hit BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Таблица для ошибок AI
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    search_query TEXT,
                    error_message TEXT,
                    vacancies_json_preview TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            print("База данных инициализирована")

    def get_cached_result(self, search_query: str, area: int = 1, max_age_hours: int = 1) -> Optional[Dict]:
        """Получение закэшированного результата (если есть и не устарел)"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT analysis_result, vacancies_count, created_at
                FROM search_cache
                WHERE search_query = ? AND area = ? AND created_at > ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (search_query, area, cutoff_time))

            row = cursor.fetchone()
            if row:
                result = json.loads(row[0])
                print(f"Кэш: найден результат для '{search_query}' от {row[2]}")
                return result
        return None

    def save_cache(self, search_query: str, area: int, vacancies_count: int, analysis_result: Dict):
        """Сохранение результата в кэш"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO search_cache (search_query, area, vacancies_count, analysis_result, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (search_query, area, vacancies_count, json.dumps(analysis_result), datetime.now()))
            conn.commit()
            print(f"Кэш: сохранен результат для '{search_query}'")

    def save_skills_analysis(self, search_query: str, analysis_result: Dict):
        """Сохранение детального анализа навыков в БД"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Сначала удаляем старые записи по этому запросу
            cursor.execute("DELETE FROM skills_analysis WHERE search_query = ?", (search_query,))

            # Сохраняем новые
            for skill_group in analysis_result.get('skills_analysis', []):
                job_title = skill_group.get('job_title', 'Все вакансии')
                for skill in skill_group.get('skills', []):
                    cursor.execute("""
                        INSERT INTO skills_analysis (search_query, job_title, skill_name, frequency, importance)
                        VALUES (?, ?, ?, ?, ?)
                    """, (search_query, job_title, skill['name'], skill['frequency'], skill['importance']))

            conn.commit()
            print(
                f"БД: сохранено {sum(len(s['skills']) for s in analysis_result.get('skills_analysis', []))} навыков")

    def save_metrics(self, search_query: str, parse_time: float, analysis_time: float,
                     vacancies_count: int, skills_count: int, cache_hit: bool = False):
        """Сохранение метрик производительности"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO performance_metrics 
                (search_query, parse_time_seconds, analysis_time_seconds, vacancies_processed, skills_found, cache_hit)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (search_query, parse_time, analysis_time, vacancies_count, skills_count, cache_hit))
            conn.commit()

    def log_ai_error(self, search_query: str, error_message: str, vacancies_json_preview: str = ""):
        """Логирование ошибок AI"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ai_errors (search_query, error_message, vacancies_json_preview)
                VALUES (?, ?, ?)
            """, (search_query, error_message, vacancies_json_preview[:500]))
            conn.commit()
            print(f" Ошибка AI залогирована: {error_message[:100]}")

    def get_statistics(self) -> Dict:
        """Получение статистики из БД"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Общая статистика
            cursor.execute("SELECT COUNT(*) FROM search_cache")
            total_searches = cursor.fetchone()[0]

            cursor.execute("SELECT AVG(parse_time_seconds) FROM performance_metrics WHERE parse_time_seconds > 0")
            avg_parse_time = cursor.fetchone()[0] or 0

            cursor.execute("SELECT AVG(analysis_time_seconds) FROM performance_metrics WHERE analysis_time_seconds > 0")
            avg_analysis_time = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM ai_errors")
            total_errors = cursor.fetchone()[0]

            return {
                "total_searches": total_searches,
                "avg_parse_time": round(avg_parse_time, 2),
                "avg_analysis_time": round(avg_analysis_time, 2),
                "total_errors": total_errors
            }


if __name__ == "__main__":
    # Тест БД
    db = Database()
    stats = db.get_statistics()
    print(f"Статистика БД: {stats}")