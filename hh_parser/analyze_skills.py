import json
import re
from collections import Counter

# Загружаем вакансии
with open('vacancies.json', 'r', encoding='utf-8') as f:
    vacancies = json.load(f)

# Расширенный словарь навыков
SKILLS = {
    # Языки программирования
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
    "PHP", "Ruby", "Swift", "Kotlin", "Scala",

    # Фреймворки
    "Django", "Flask", "FastAPI", "React", "Vue", "Angular", "Spring",
    "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy",

    # Базы данных
    "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
    "ClickHouse", "Oracle", "Cassandra",

    # DevOps и инструменты
    "Docker", "Kubernetes", "Git", "Linux", "Bash", "Jenkins", "GitLab CI",
    "GitHub Actions", "Nginx", "Apache", "Terraform", "Ansible",

    # Облачные технологии
    "AWS", "Azure", "GCP", "Yandex Cloud", "S3", "Lambda",

    # Тестирование
    "pytest", "unittest", "Selenium", "Postman", "JMeter",

    # API и протоколы
    "REST API", "GraphQL", "gRPC", "RabbitMQ", "Kafka", "Celery",

    # Методологии
    "Agile", "Scrum", "Kanban", "CI/CD", "TDD",

    # Аналитика и ML
    "Machine Learning", "Data Science", "NLP", "Computer Vision",
    "Deep Learning", "Статистика", "Tableau", "Power BI"
}

# Приводим к нижнему регистру для поиска
skills_lower = {skill.lower(): skill for skill in SKILLS}


def extract_skills(text):
    """Извлекает навыки из текста"""
    if not text:
        return []
    text = text.lower()
    found = set()
    for skill_key, skill_name in skills_lower.items():
        if skill_key in text:
            found.add(skill_name)
    return list(found)


print(f" Анализ {len(vacancies)} вакансий...")
print("-" * 50)

# Анализируем каждую вакансию
skill_counter = Counter()
total_vacancies = len(vacancies)

for vacancy in vacancies:
    # Собираем текст из разных полей
    text_parts = []

    if vacancy.get('name'):
        text_parts.append(vacancy['name'])
    if vacancy.get('description'):
        text_parts.append(vacancy['description'])

    snippet = vacancy.get('snippet', {})
    if snippet.get('requirement'):
        text_parts.append(snippet['requirement'])

    full_text = ' '.join(text_parts)

    # Извлекаем навыки
    skills = extract_skills(full_text)
    for skill in set(skills):  # Каждый навык считаем 1 раз на вакансию
        skill_counter[skill] += 1

# Выводим результаты
print("\n ТОП-15 НАВЫКОВ ПО ЧАСТОТНОСТИ:")
print("-" * 50)

for i, (skill, count) in enumerate(skill_counter.most_common(15), 1):
    frequency = (count / total_vacancies) * 100

    if frequency > 70:
        importance = " ОБЯЗАТЕЛЬНЫЙ"
    elif frequency > 40:
        importance = "РЕКОМЕНДУЕМЫЙ"
    else:
        importance = " ЖЕЛАТЕЛЬНЫЙ"

    print(f"{i:2}. {skill}: {frequency:5.1f}% {importance}")

# Дополнительная статистика
print("\n" + "=" * 50)
print("ДОПОЛНИТЕЛЬНАЯ СТАТИСТИКА:")
print("=" * 50)

# Навыки, которые встречаются в 100% вакансий
mandatory_skills = [(s, c) for s, c in skill_counter.most_common()
                    if (c / total_vacancies) * 100 >= 100]

if mandatory_skills:
    print("\nОбязательные навыки (100% вакансий):")
    for skill, count in mandatory_skills:
        print(f"   - {skill}")

# Навыки с низкой частотностью (редкие, но могут быть важны)
rare_skills = [(s, c) for s, c in skill_counter.most_common()
               if (c / total_vacancies) * 100 < 20 and c > 0]

if rare_skills:
    print("\n🟢 Редкие навыки (менее 20% вакансий):")
    for skill, count in rare_skills[:5]:
        freq = (count / total_vacancies) * 100
        print(f"   - {skill}: {freq:.1f}%")

# Сохраняем результат
result = {
    "total_vacancies": total_vacancies,
    "skills": [
        {
            "name": skill,
            "frequency": round((count / total_vacancies) * 100, 1),
            "count": count
        }
        for skill, count in skill_counter.most_common()
    ]
}

with open('analysis_result.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"\nРезультат сохранен в analysis_result.json")
print(f"\n Анализ завершен!")