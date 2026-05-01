# -*- coding: utf-8 -*-
# analyze_skills.py

import json
import re
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
    analyze vacancies from dict (not from file)
    
    Args:
        vacancies: list of vacancy dicts
    
    Returns:
        dict with analysis results
    """
    skill_counter = Counter()
    total_vacancies = len(vacancies)
    
    for vacancy in vacancies:
        # collect text from different fields
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
        
        # extract skills
        skills = extract_skills(full_text)
        for skill in set(skills):
            skill_counter[skill] += 1
    
    # build result
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


def analyze_vacancies_file(input_file: str = "vacancies.json", output_file: str = "analysis_result.json"):
    """
    analyze vacancies from JSON file and save results
    
    Args:
        input_file: path to input JSON file with vacancies
        output_file: path to output JSON file with analysis results
    """
    # load vacancies
    with open(input_file, 'r', encoding='utf-8') as f:
        vacancies_data = json.load(f)
    
    # extract items (handle both formats)
    if isinstance(vacancies_data, dict) and 'items' in vacancies_data:
        vacancies = vacancies_data['items']
    elif isinstance(vacancies_data, list):
        vacancies = vacancies_data
    else:
        raise ValueError(f"Unexpected JSON format in {input_file}")
    
    print(f"Analyzing {len(vacancies)} vacancies...")
    print("-" * 50)
    
    # analyze
    result = analyze_vacancies_dict(vacancies)
    
    # print results
    print("\nTOP-15 SKILLS BY FREQUENCY:")
    print("-" * 50)
    
    for i, skill_info in enumerate(result['skills'][:15], 1):
        skill = skill_info['name']
        frequency = skill_info['frequency']
        
        if frequency > 70:
            importance = "MANDATORY"
        elif frequency > 40:
            importance = "RECOMMENDED"
        else:
            importance = "DESIRABLE"
        
        print(f"{i:2}. {skill}: {frequency:5.1f}% {importance}")
    
    # additional statistics
    print("\n" + "=" * 50)
    print("ADDITIONAL STATISTICS:")
    print("=" * 50)
    
    # skills that appear in 100% of vacancies
    mandatory_skills = [s for s in result['skills'] if s['frequency'] >= 100]
    
    if mandatory_skills:
        print("\nMandatory skills (100% of vacancies):")
        for skill_info in mandatory_skills:
            print(f"   - {skill_info['name']}")
    
    # rare skills (less than 20%)
    rare_skills = [s for s in result['skills'] if s['frequency'] < 20]
    
    if rare_skills:
        print("\nRare skills (less than 20% of vacancies):")
        for skill_info in rare_skills[:5]:
            print(f"   - {skill_info['name']}: {skill_info['frequency']:.1f}%")
    
    # save result
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\nResult saved to {output_file}")
    print("\nAnalysis completed!")
    
    return result


# этот код выполняется только при прямом запуске (не при импорте)
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "vacancies.json"
    
    analyze_vacancies_file(input_file)