# hh_parser/run_analysis.py
import sys
import os
import json
from pathlib import Path

# Добавляем корневую папку для импорта DataBase
sys.path.insert(0, str(Path(__file__).parent.parent))

# Импортируем наши модули
from parse_vacancies import fetch_vacancies, save_to_file
from ai_assistant import AIAssistant
from db_service import DatabaseService


def run_full_analysis(query: str, user_email: str = "test@example.com",
                      area: int = 1, per_page: int = 20, branch_type: int = 1):
    """
    Полный цикл анализа:
    1. Получение вакансий с hh.ru
    2. AI-анализ навыков
    3. Сохранение в БД
    """
    print("\n" + "=" * 60)
    print(f"🚀 ЗАПУСК АНАЛИЗА: {query}")
    print("=" * 60)

    # Шаг 1: Получение вакансий
    print("\n📥 Шаг 1: Получение вакансий с hh.ru...")
    vacancies_data = fetch_vacancies(query=query, area=area, per_page=per_page)

    if vacancies_data.get('error'):
        print(f"❌ Ошибка: {vacancies_data.get('message')}")
        return None

    vacancies = vacancies_data.get('items', [])
    print(f"✅ Получено {len(vacancies)} вакансий")

    # Сохраняем сырые данные
    safe_query = query.replace(' ', '_')
    save_to_file(vacancies_data, f"vacancies_{safe_query}.json")

    # Шаг 2: AI-анализ
    print("\n🤖 Шаг 2: AI-анализ навыков...")
    ai = AIAssistant()
    analysis_result = ai.analyze_vacancies(vacancies, branch_type="single")

    skills_count = len(analysis_result.get('skills_analysis', [{}])[0].get('skills', []))
    print(f"✅ Анализ завершён, найдено навыков: {skills_count}")

    # Сохраняем результат
    with open(f"analysis_{safe_query}.json", 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=2)

    # Шаг 3: Сохранение в БД
    print("\n💾 Шаг 3: Сохранение в базу данных...")
    db_service = DatabaseService()

    # Получаем user_id по email (нужно доработать)
    # Пока используем user_id=1
    user_id = 1

    result = db_service.save_analysis_result(
        user_id=user_id,
        query=query,
        branch_type=branch_type,
        analysis_result=analysis_result,
        vacancies_count=len(vacancies)
    )

    if result['success']:
        print(f"\n🎉 УСПЕХ! Сессия #{result['session_id']}")
        print(f"   Сохранено навыков: {result['skills_saved']}")
    else:
        print(f"❌ Ошибка: {result.get('error')}")

    return result


if __name__ == "__main__":
    # Получаем запрос из аргументов
    if len(sys.argv) > 1:
        query = ' '.join(sys.argv[1:])
    else:
        query = input("Введите поисковый запрос: ").strip()
        if not query:
            query = "Python разработчик"

    run_full_analysis(query=query, area=1, per_page=20)