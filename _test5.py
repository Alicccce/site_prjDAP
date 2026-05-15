from services.qwen_service import _inject_resources, _get_all_resources

# Тест 1: Python 4 недели — нет дублей
plan = {"weeks": [
    {"week": i, "theme": "Python", "skills": ["Python"], "goal": "...", "mentor_tip": "..."}
    for i in range(1, 5)
]}
result = _inject_resources(plan, "free")
all_urls = [r["url"] for w in result["weeks"] for r in w["resources"]]
dupes = [u for u in set(all_urls) if all_urls.count(u) > 1]
print(f"Python 4 недели — дублей: {len(dupes)} ({'OK' if not dupes else dupes})")
for w in result["weeks"]:
    print(f"  Неделя {w['week']}: {w['resources'][0]['title'][:55]}")

# Тест 2: Неизвестные навыки
print("\nНеизвестные навыки:")
for skill in ["Microservices", "C++", "Kafka", "Terraform", "GraphQL"]:
    res = _get_all_resources(skill)
    print(f"  {skill:15} → {res[0]['title'][:55]}")
