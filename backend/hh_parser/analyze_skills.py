# -*- coding: utf-8 -*-
# analyze_skills.py

import json
from collections import Counter

# расширенный словарь навыков
SKILLS = {
    # языки программирования
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
    "PHP", "Ruby", "Swift", "Kotlin", "Scala",

    # фреймворки
    "Django", "Flask", "FastAPI", "React", "Vue", "Angular", "Spring",
    "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy",

    # базы данных
    "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
    "ClickHouse", "Oracle", "Cassandra",

    # devops и инструменты
    "Docker", "Kubernetes", "Git", "Linux", "Bash", "Jenkins", "GitLab CI",
    "GitHub Actions", "Nginx", "Apache", "Terraform", "Ansible",

    # облачные технологии
    "AWS", "Azure", "GCP", "Yandex Cloud", "S3", "Lambda",

    # тестирование
    "pytest", "unittest", "Selenium", "Postman", "JMeter",

    # api и протоколы
    "REST API", "GraphQL", "gRPC", "RabbitMQ", "Kafka", "Celery",

    # методологии
    "Agile", "Scrum", "Kanban", "CI/CD", "TDD",

    # аналитика и ml
    "Machine Learning", "Data Science", "NLP", "Computer Vision",
    "Deep Learning", "Statistics", "Tableau", "Power BI"
}

# приводим к нижнему регистру для поиска
skills_lower = {skill.lower(): skill for skill in SKILLS}


def extract_skills(text):
    """extracts skills from text"""
    if not text:
        return []
    text = text.lower()
    found = set()
    for skill_key, skill_name in skills_lower.items():
        if skill_key in text:
            found.add(skill_name)
    return list(found)


def analyze_vacancies_dict(vacancies):
    """
    analyze vacancies from dict

    Args:
        vacancies: list of vacancy dicts

    Returns:
        dict with analysis results
    """
    skill_counter = Counter()
    total_vacancies = len(vacancies)

    for vacancy in vacancies:
        text_parts = []

        if vacancy.get('name'):
            text_parts.append(vacancy['name'])
        if vacancy.get('description'):
            text_parts.append(vacancy['description'])

        snippet = vacancy.get('snippet', {})
        if snippet.get('requirement'):
            text_parts.append(snippet['requirement'])
        if snippet.get('responsibility'):
            text_parts.append(snippet['responsibility'])

        full_text = ' '.join(text_parts)
        skills = extract_skills(full_text)

        for skill in set(skills):
            skill_counter[skill] += 1

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

    return result


def analyze_vacancies_file(input_file="vacancies.json", output_file="analysis_result.json"):
    """analyze vacancies from JSON file and save results"""
    with open(input_file, 'r', encoding='utf-8') as f:
        vacancies_data = json.load(f)

    if isinstance(vacancies_data, dict) and 'items' in vacancies_data:
        vacancies = vacancies_data['items']
    elif isinstance(vacancies_data, list):
        vacancies = vacancies_data
    else:
        raise ValueError(f"Unexpected JSON format in {input_file}")

    result = analyze_vacancies_dict(vacancies)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Analysis saved to {output_file}")
    return result


# этот код выполняется только при прямом запуске (не при импорте)
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "vacancies.json"

    analyze_vacancies_file(input_file)
