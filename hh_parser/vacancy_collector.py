# vacancy_collector.py
import requests
import json
import time
from typing import List, Dict, Any


class VacancyCollector:
    """Сборщик вакансий с API hh.ru"""

    def __init__(self, access_token: str):
        self.base_url = "https://api.hh.ru"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "PersonalizedCareerNavigator/1.0"
        }

    def search_vacancies(self,
                         search_text: str = None,
                         area: int = 1,
                         per_page: int = 50,
                         pages: int = 1) -> List[Dict]:
        """
        Поиск вакансий по ключевым словам

        Args:
            search_text: Поисковый запрос (например, "Python разработчик")
            area: ID региона (1 - Москва, 2 - СПб, 113 - Россия)
            per_page: Количество на странице (макс 100)
            pages: Количество страниц

        Returns:
            Список вакансий
        """
        if search_text is None:
            search_text = "Python разработчик"

        all_vacancies = []
        url = f"{self.base_url}/vacancies"

        print(f"\n🔍 Поиск вакансий: '{search_text}'")
        print(f"📍 Регион: {self._get_area_name(area)}")
        print("-" * 50)

        for page in range(pages):
            params = {
                "text": search_text,
                "area": area,
                "per_page": per_page,
                "page": page
            }

            print(f"📥 Страница {page + 1}...", end=" ")

            try:
                response = requests.get(url, headers=self.headers, params=params)
                time.sleep(0.5)

                if response.status_code == 200:
                    data = response.json()
                    vacancies_on_page = data.get('items', [])

                    if not vacancies_on_page:
                        print("нет данных")
                        break

                    # Загружаем детальную информацию по каждой вакансии
                    for vacancy in vacancies_on_page:
                        full_info = self._get_vacancy_details(vacancy['id'])
                        if full_info:
                            all_vacancies.append(full_info)
                        time.sleep(0.2)

                    print(f"✅ {len(vacancies_on_page)} вакансий")

                    if page >= data.get('pages', 0) - 1:
                        break
                else:
                    print(f"❌ ошибка {response.status_code}")
                    break

            except Exception as e:
                print(f"❌ ошибка: {e}")
                break

        print(f"\n📊 ИТОГО загружено: {len(all_vacancies)} вакансий")
        return all_vacancies

    def _get_area_name(self, area_id: int) -> str:
        """Получение названия региона по ID"""
        areas = {1: "Москва", 2: "Санкт-Петербург", 113: "Россия"}
        return areas.get(area_id, f"ID {area_id}")

    def _get_vacancy_details(self, vacancy_id: str) -> Dict:
        """Получение детальной информации по вакансии"""
        url = f"{self.base_url}/vacancies/{vacancy_id}"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"   ⚠️ Ошибка загрузки вакансии {vacancy_id}: {e}")
        return None

    def save_vacancies(self, vacancies: List[Dict], filename: str = "vacancies.json"):
        """Сохранение вакансий в JSON файл"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(vacancies, f, indent=2, ensure_ascii=False)
        print(f"💾 {len(vacancies)} вакансий сохранено в {filename}")


if __name__ == "__main__":
    # Тестирование сборщика
    from auth import load_or_refresh_token

    token_data = load_or_refresh_token()
    collector = VacancyCollector(token_data['access_token'])

    vacancies = collector.search_vacancies("Python разработчик", pages=1)
    collector.save_vacancies(vacancies)