import requests
import json

# Читаем токен из файла
with open('token.txt', 'r') as f:
    TOKEN = f.read().strip()

# Заголовки для запроса
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "User-Agent": "MyParser/1.0"
}

print("Поиск вакансий Python разработчика...")
print("-" * 50)

# Поиск вакансий
url = "https://api.hh.ru/vacancies"
params = {
    "text": "Python разработчик",
    "area": 1,  # 1 = Москва
    "per_page": 20  # сколько вакансий загрузить
}

response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    data = response.json()
    vacancies = data.get('items', [])

    print(f"Найдено вакансий: {len(vacancies)}")
    print()

    # Выводим информацию по каждой вакансии
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

    # Сохраняем в файл
    with open('vacancies.json', 'w', encoding='utf-8') as f:
        json.dump(vacancies, f, ensure_ascii=False, indent=2)

    print("Вакансии сохранены в vacancies.json")

else:
    print(f"Ошибка: {response.status_code}")
    print(response.text)