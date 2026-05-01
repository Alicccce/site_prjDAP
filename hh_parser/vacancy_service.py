# vacancy_service.py
import json
import time
from typing import Dict, List, Optional
from datetime import datetime

from database import Database
from vacancy_collector import VacancyCollector
from ai_assistant import AIAssistant


class VacancyAnalysisService:
    """Сервис для анализа вакансий с кэшированием и метриками"""

    def __init__(self, access_token: str):
        self.collector = VacancyCollector(access_token)
        self.ai_assistant = AIAssistant()
        self.db = Database()
        self.max_vacancies = 50  # Ограничение на количество анализируемых вакансий

    def analyze(self,
                search_query: str,
                area: int = 1,
                use_cache: bool = True,
                max_vacancies: Optional[int] = None) -> Dict:
        """
        Основной метод анализа вакансий

        Args:
            search_query: Поисковый запрос (например, "Python разработчик")
            area: ID региона (1 - Москва)
            use_cache: Использовать ли кэш
            max_vacancies: Максимальное количество вакансий для анализа (по умолчанию 50)

        Returns:
            Результат анализа в формате:
            {
                "success": True,
                "data": {...},  # результат от AIAssistant
                "metrics": {...},  # метрики производительности
                "from_cache": False
            }
        """
        if max_vacancies is None:
            max_vacancies = self.max_vacancies

        result = {
            "success": False,
            "data": None,
            "metrics": {},
            "from_cache": False,
            "errors": []
        }

        # Шаг 1: Проверка кэша
        if use_cache:
            cached = self.db.get_cached_result(search_query, area)
            if cached:
                result["data"] = cached
                result["success"] = True
                result["from_cache"] = True
                result["metrics"]["cache_hit"] = True

                # Сохраняем метрику для кэша
                self.db.save_metrics(
                    search_query, 0, 0,
                    cached.get('total_vacancies', 0),
                    self._count_total_skills(cached),
                    cache_hit=True
                )

                print(f"✅ Результат получен из кэша для '{search_query}'")
                return result

        # Шаг 2: Парсинг hh.ru
        print(f"\n🔍 Начинаем анализ для запроса: '{search_query}'")
        print("-" * 50)

        parse_start = time.time()

        try:
            vacancies = self.collector.search_vacancies(
                search_text=search_query,
                area=area,
                per_page=min(max_vacancies, 100),
                pages=1  # Берем только первую страницу для скорости
            )
        except Exception as e:
            error_msg = f"Ошибка при парсинге hh.ru: {str(e)}"
            print(f"❌ {error_msg}")
            result["errors"].append(error_msg)
            self.db.log_ai_error(search_query, error_msg)
            return result

        parse_time = time.time() - parse_start

        if not vacancies:
            error_msg = "Вакансии не найдены"
            print(f"⚠️ {error_msg}")
            result["errors"].append(error_msg)
            return result

        # Ограничиваем количество вакансий для анализа
        original_count = len(vacancies)
        if len(vacancies) > max_vacancies:
            vacancies = vacancies[:max_vacancies]
            print(f"⚠️ Ограничение: анализируем {max_vacancies} из {original_count} вакансий")

        # Шаг 3: AI-анализ
        analysis_start = time.time()

        try:
            analysis_result = self.ai_assistant.analyze_vacancies(vacancies, branch_type="single")
        except Exception as e:
            error_msg = f"Ошибка при AI-анализе: {str(e)}"
            print(f"❌ {error_msg}")
            result["errors"].append(error_msg)
            self.db.log_ai_error(search_query, error_msg, json.dumps(vacancies[:2]))
            return result

        analysis_time = time.time() - analysis_start

        # Проверка: удалось ли выделить навыки?
        total_skills = self._count_total_skills(analysis_result)
        if total_skills == 0:
            error_msg = "AI не смог выделить ни одного навыка из вакансий"
            print(f"⚠️ {error_msg}")
            result["errors"].append(error_msg)
            self.db.log_ai_error(search_query, error_msg, json.dumps(vacancies[:2]))

        # Шаг 4: Сохранение в БД
        self.db.save_cache(search_query, area, len(vacancies), analysis_result)
        self.db.save_skills_analysis(search_query, analysis_result)
        self.db.save_metrics(
            search_query,
            parse_time,
            analysis_time,
            len(vacancies),
            total_skills,
            cache_hit=False
        )

        # Шаг 5: Формирование результата
        result["success"] = True
        result["data"] = analysis_result
        result["metrics"] = {
            "parse_time_seconds": round(parse_time, 2),
            "analysis_time_seconds": round(analysis_time, 2),
            "total_time_seconds": round(parse_time + analysis_time, 2),
            "vacancies_processed": len(vacancies),
            "skills_found": total_skills,
            "cache_hit": False
        }

        print("\n" + "=" * 50)
        print("✅ АНАЛИЗ ЗАВЕРШЕН")
        print(f"   Вакансий обработано: {len(vacancies)}")
        print(f"   Навыков найдено: {total_skills}")
        print(f"   Время парсинга: {parse_time:.2f} сек")
        print(f"   Время анализа: {analysis_time:.2f} сек")
        print("=" * 50)

        return result

    def _count_total_skills(self, analysis_result: Dict) -> int:
        """Подсчет общего количества найденных навыков"""
        total = 0
        for skill_group in analysis_result.get('skills_analysis', []):
            total += len(skill_group.get('skills', []))
        return total

    def get_top_skills(self, search_query: str, limit: int = 10) -> List[Dict]:
        """Получение топ-навыков по запросу из БД"""
        import sqlite3

        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT skill_name, frequency, importance
                FROM skills_analysis
                WHERE search_query = ?
                ORDER BY frequency DESC
                LIMIT ?
            """, (search_query, limit))

            return [{"name": row[0], "frequency": row[1], "importance": row[2]}
                    for row in cursor.fetchall()]

    def clear_cache(self, search_query: Optional[str] = None):
        """Очистка кэша (по запросу или всего)"""
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            if search_query:
                cursor.execute("DELETE FROM search_cache WHERE search_query = ?", (search_query,))
                print(f"🗑️ Кэш очищен для запроса '{search_query}'")
            else:
                cursor.execute("DELETE FROM search_cache")
                print("🗑️ Весь кэш очищен")
            conn.commit()


def demo():
    """Демонстрация работы сервиса"""
    from auth import load_or_refresh_token

    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║     Vacancy Analysis Service - Тестирование                  ║
    ║     hh.ru → AI → БД с кэшированием и метриками              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    # Загрузка токена
    token_data = load_or_refresh_token()
    access_token = token_data['access_token']

    # Создание сервиса
    service = VacancyAnalysisService(access_token)

    # Тестовый запрос
    search_query = input("\n🔍 Введите должность для поиска (Enter для 'Python разработчик'): ").strip()
    if not search_query:
        search_query = "Python разработчик"

    # Первый запуск (с парсингом)
    print("\n" + "=" * 50)
    print("📊 ПЕРВЫЙ ЗАПРОС (будет выполнен парсинг hh.ru)")
    print("=" * 50)

    result1 = service.analyze(search_query, use_cache=False)  # Принудительно без кэша

    if result1["success"]:
        data = result1["data"]
        metrics = result1["metrics"]

        print(f"\n📊 РЕЗУЛЬТАТЫ АНАЛИЗА:")
        print(f"   Должности: {', '.join(data.get('job_titles', []))}")
        print(f"   Всего вакансий: {data.get('total_vacancies', 0)}")

        # Вывод топ-навыков
        if data.get('skills_analysis'):
            skills = data['skills_analysis'][0].get('skills', [])[:10]
            print(f"\n   🛠️ ТОП-10 НАВЫКОВ:")
            for i, skill in enumerate(skills, 1):
                icon = "🔴" if skill['importance'] == 'mandatory' else "🟡" if skill[
                                                                                 'importance'] == 'recommended' else "🟢"
                print(f"      {i}. {icon} {skill['name']}: {skill['frequency']}%")

        print(f"\n   ⏱️ Метрики:")
        print(f"      Парсинг hh.ru: {metrics.get('parse_time_seconds', 0)} сек")
        print(f"      AI анализ: {metrics.get('analysis_time_seconds', 0)} сек")
        print(f"      Всего: {metrics.get('total_time_seconds', 0)} сек")
    else:
        print(f"\n❌ Ошибка: {result1.get('errors', ['Неизвестная ошибка'])[0]}")

    # Второй запуск (из кэша)
    print("\n" + "=" * 50)
    print("📊 ВТОРОЙ ЗАПРОС (должен взять из кэша)")
    print("=" * 50)

    result2 = service.analyze(search_query, use_cache=True)

    if result2["success"]:
        if result2["from_cache"]:
            print("✅ Результат успешно получен из кэша!")
            print(f"   Навыков в кэше: {service._count_total_skills(result2['data'])}")
        else:
            print("⚠️ Кэш не использовался (возможно, запрос не найден или устарел)")

    # Показ статистики из БД
    stats = service.db.get_statistics()
    print("\n" + "=" * 50)
    print("📊 СТАТИСТИКА БАЗЫ ДАННЫХ:")
    print("=" * 50)
    print(f"   Всего поисков: {stats['total_searches']}")
    print(f"   Среднее время парсинга: {stats['avg_parse_time']} сек")
    print(f"   Среднее время AI анализа: {stats['avg_analysis_time']} сек")
    print(f"   Всего ошибок AI: {stats['total_errors']}")

    # Топ-навыки из БД
    top_skills = service.get_top_skills(search_query)
    if top_skills:
        print(f"\n   🏆 ТОП-НАВЫКИ ИЗ БД (запрос: {search_query}):")
        for i, skill in enumerate(top_skills[:5], 1):
            print(f"      {i}. {skill['name']}: {skill['frequency']}% ({skill['importance']})")

    print("\n✅ Демонстрация завершена!")


if __name__ == "__main__":
    demo()