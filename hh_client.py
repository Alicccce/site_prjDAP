import requests
import random

# Список User-Agent для ротации
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15",
]


def fetch_vacancies_from_hh(query, city="Россия", experience="нет опыта"):
    # ID городов
    cities = {"Москва": 1, "Санкт-Петербург": 2, "Россия": 113}
    city_id = cities.get(city, 113)

    # Опыт работы
    exp_values = {"нет опыта": "noExperience", "от 1 года до 3 лет": "between1And3",
                  "от 3 до 6 лет": "between3And6", "более 6 лет": "moreThan6"}
    exp_value = exp_values.get(experience, "noExperience")

    # Формируем URL с параметрами
    url = f"https://api.hh.ru/vacancies?text={query}&area={city_id}&experience={exp_value}&per_page=10"

    # Случайный User-Agent
    headers = {"User-Agent": random.choice(USER_AGENTS)}

    try:
        # Отправляем GET-запрос
        response = requests.get(url, headers=headers, timeout=10)

        # Проверяем, что ответ успешный
        if response.status_code == 200:
            data = response.json()

            # Выводим результат
            print(f"\n Поиск: {query}, {city}, {experience}")
            print(f"Найдено вакансий: {data.get('found', 0)}\n")

            for item in data.get("items", []):
                print(f"{item.get('name')}")
                print(f"   Компания: {item.get('employer', {}).get('name')}")
                print(f"   Город: {item.get('area', {}).get('name')}")
                print(f"   Требования: {item.get('snippet', {}).get('requirement', 'Не указано')[:100]}...")
                print("-" * 40)

            return data  # Возвращаем JSON для дальнейшей работы

        else:
            print(f"Ошибка: {response.status_code}")
            return None

    except requests.exceptions.Timeout:
        print("Ошибка: hh.ru не отвечает")
        return None
    except requests.exceptions.ConnectionError:
        print("Ошибка: нет соединения с hh.ru")
        return None
    except Exception as e:
        print(f"Ошибка: {e}")
        return None


# Запуск программы
if __name__ == "__main__":
    print("=" * 50)
    print("ПОИСК ВАКАНСИЙ НА hh.ru")
    print("=" * 50)

    # Пример 1
    fetch_vacancies_from_hh("Python-разработчик", "Москва", "нет опыта")

    # Пример 2
    fetch_vacancies_from_hh("Data Scientist", "Санкт-Петербург", "от 1 года до 3 лет")

    # Сохраняем пример ответа в файл
    print("\n Сохраняю пример ответа в файл vacancies_sample.json")
    data = fetch_vacancies_from_hh("Python-разработчик", "Москва", "нет опыта")
    if data:
        import json

        with open("vacancies_sample.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("Файл vacancies_sample.json создан")