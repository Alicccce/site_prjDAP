import requests
import json
from typing import Dict, List, Optional, Any

# Константы
TOKEN_FILE = 'token.txt'
DEFAULT_USER_AGENT = "MyParser/1.0"


def get_token() -> Optional[str]:
    """Загружает токен из файла"""
    try:
        with open(TOKEN_FILE, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def fetch_vacancies(
        query: str,
        area: int = 1,
        per_page: int = 20,
        page: int = 0
) -> Dict[str, Any]:
    """
    Получает вакансии с hh.ru

    Args:
        query: Поисковый запрос (например, "Python разработчик")
        area: ID региона (1 - Москва, 2 - СПб, 113 - Россия)
        per_page: Количество вакансий на странице (макс 100)
        page: Номер страницы

    Returns:
        Dict с данными от API hh.ru

    Example:
        >>> result = fetch_vacancies("Data Scientist", area=1, per_page=10)
        >>> print(len(result['items']))
        10
    """

    # Получаем токен (если есть)
    token = get_token()

    # Формируем заголовки
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Параметры запроса
    params = {
        "text": query,
        "area": area,
        "per_page": min(per_page, 100),  # API ограничивает 100
        "page": page
    }

    # Выполняем запрос
    response = requests.get(
        "https://api.hh.ru/vacancies",
        headers=headers,
        params=params,
        timeout=10
    )

    # Проверяем ответ
    if response.status_code == 200:
        return response.json()
    else:
        # Возвращаем структуру с ошибкой
        return {
            "error": True,
            "status_code": response.status_code,
            "message": response.text,
            "items": [],
            "found": 0
        }


def save_to_file(data: Dict, filename: str = "vacancies.json") -> None:
    """Сохраняет данные в JSON файл"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================
# Только для тестирования (не выполняется при импорте)
# ============================================

if __name__ == "__main__":
    # Этот код запускается только если файл запущен напрямую
    # При импорте через import — этот код НЕ выполнится

    import sys

    # Получаем запрос из аргументов или ввода
    if len(sys.argv) > 1:
        query = ' '.join(sys.argv[1:])
    else:
        query = input("Введите поисковый запрос: ")
        if not query:
            query = "Python разработчик"

    print(f"Поиск: {query}")
    print("-" * 50)

    # Используем функцию
    result = fetch_vacancies(query, area=1, per_page=20)

    if result.get('error'):
        print(f"Ошибка: {result.get('message')}")
    else:
        vacancies = result.get('items', [])
        print(f"Найдено вакансий: {len(vacancies)}")

        for i, vacancy in enumerate(vacancies, 1):
            print(f"{i}. {vacancy.get('name')}")
            print(f"   Компания: {vacancy.get('employer', {}).get('name')}")
            print(f"   Город: {vacancy.get('area', {}).get('name')}")

            salary = vacancy.get('salary')
            if salary:
                salary_text = f"{salary.get('from', '')} - {salary.get('to', '')} {salary.get('currency', '')}"
                print(f"   Зарплата: {salary_text.strip()}")
            else:
                print(f"   Зарплата: не указана")

            print(f"   Ссылка: {vacancy.get('alternate_url')}")
            print()

        save_to_file(result)
        print("Вакансии сохранены в vacancies.json")