#!/usr/bin/env python3
"""
Demonstration of the complete AI-integrated vacancy analysis workflow
"""

from vacancy_analysis_service import VacancyAnalysisService
from ai_assistant import AIAssistant
from models import SkillsPosition, Skill, SkillImportance


def demo_complete_workflow():
    """Demonstrate the complete workflow with sample data"""
    print("=" * 60)
    print("AI-INTEGRATED VACANCY ANALYSIS DEMO")
    print("=" * 60)
    
    # Initialize services
    vacancy_service = VacancyAnalysisService(cache_duration_hours=1, max_vacancies=10)
    ai_assistant = AIAssistant()
    
    print("\n1. ANALYZING JOB POSITIONS")
    print("-" * 30)
    
    # Create sample job analyses (simulating hh.ru data)
    job_analyses = [
        SkillsPosition(
            position_name="Data Scientist",
            skills=[
                Skill("Python", SkillImportance.MANDATORY, 90),
                Skill("Machine Learning", SkillImportance.MANDATORY, 80),
                Skill("SQL", SkillImportance.RECOMMENDED, 70),
                Skill("Statistics", SkillImportance.RECOMMENDED, 60),
                Skill("TensorFlow", SkillImportance.OPTIONAL, 40),
                Skill("Docker", SkillImportance.OPTIONAL, 30)
            ],
            total_vacancies_analyzed=15,
            search_query="Data Scientist"
        ),
        SkillsPosition(
            position_name="Python Developer",
            skills=[
                Skill("Python", SkillImportance.MANDATORY, 100),
                Skill("Django", SkillImportance.RECOMMENDED, 60),
                Skill("PostgreSQL", SkillImportance.RECOMMENDED, 50),
                Skill("REST API", SkillImportance.RECOMMENDED, 70),
                Skill("Docker", SkillImportance.OPTIONAL, 35),
                Skill("JavaScript", SkillImportance.OPTIONAL, 25)
            ],
            total_vacancies_analyzed=12,
            search_query="Python Developer"
        ),
        SkillsPosition(
            position_name="ML Engineer",
            skills=[
                Skill("Python", SkillImportance.MANDATORY, 95),
                Skill("TensorFlow", SkillImportance.MANDATORY, 70),
                Skill("PyTorch", SkillImportance.RECOMMENDED, 60),
                Skill("Machine Learning", SkillImportance.MANDATORY, 85),
                Skill("Docker", SkillImportance.RECOMMENDED, 55),
                Skill("Kubernetes", SkillImportance.OPTIONAL, 30)
            ],
            total_vacancies_analyzed=8,
            search_query="ML Engineer"
        )
    ]
    
    # Display analyzed positions
    for job in job_analyses:
        print(f"\n[ANALYSIS] {job.position_name} ({job.total_vacancies_analyzed} vacancies analyzed)")
        mandatory = [s.name for s in job.skills if s.importance == SkillImportance.MANDATORY]
        recommended = [s.name for s in job.skills if s.importance == SkillImportance.RECOMMENDED]
        optional = [s.name for s in job.skills if s.importance == SkillImportance.OPTIONAL]
        
        print(f"   [MANDATORY] {', '.join(mandatory)}")
        print(f"   [RECOMMENDED] {', '.join(recommended)}")
        print(f"   [OPTIONAL] {', '.join(optional)}")
    
    print("\n2. USER SKILL MATCHING")
    print("-" * 30)
    
    # Define user skills
    user_skills = ["Python", "SQL", "Docker", "Git"]
    print(f"[USER] User Skills: {', '.join(user_skills)}")
    
    # Match skills with jobs
    matches = ai_assistant.matchUserSkillsWithJobs(user_skills, job_analyses)
    
    print(f"[MATCHES] MATCH RESULTS ({len(matches)} matches found):")
    print("-" * 50)
    
    for i, match in enumerate(matches, 1):
        match_icon = "[HIGH]" if match.match_percentage >= 70 else "[MED]" if match.match_percentage >= 50 else "[LOW]"
        print(f"{i}. {match.job_title:<20} {match.match_percentage:5.1f}% {match_icon}")
        
        if match.matched_skills:
            print(f"   [MATCHED] Matched: {', '.join(match.matched_skills)}")
        
        if match.missing_mandatory:
            print(f"   [MISSING_MANDATORY] Missing mandatory: {', '.join(match.missing_mandatory)}")
        elif match.missing_skills:
            missing = match.missing_skills[:3]
            if len(match.missing_skills) > 3:
                missing.append(f"+{len(match.missing_skills)-3} more")
            print(f"   [MISSING] Missing: {', '.join(missing)}")
        print()
    
    print("\n3. SKILL RECOMMENDATIONS")
    print("-" * 30)
    
    # Get recommendations
    recommendations = ai_assistant.getSkillRecommendations(user_skills, job_analyses, limit=5)
    
    if recommendations:
        print(f"[RECOMMENDATIONS] TOP {len(recommendations)} SKILLS TO LEARN:")
        print("-" * 40)
        
        for i, rec in enumerate(recommendations, 1):
            importance_icon = "[MANDATORY]" if rec['importance'] == "mandatory" else "[RECOMMENDED]" if rec['importance'] == "recommended" else "[OPTIONAL]"
            print(f"{i}. {rec['name']:<20} {rec['frequency']:5.1f}% {importance_icon}")
            print(f"   [STATS] Appears in {rec['job_count']} positions, score: {rec['score']}")
            print()
    else:
        print("[SUCCESS] You already have all the recommended skills!")
    
    print("\n4. PERFORMANCE METRICS")
    print("-" * 30)
    
    # Show cache stats
    cache_stats = vacancy_service.get_cache_stats()
    print(f"[CACHE] Cache: {cache_stats['active_entries']} active entries")
    print(f"[CACHE] Cache duration: {cache_stats['cache_duration_hours']} hours")
    
    # Show metrics if available
    metrics = vacancy_service.get_metrics()
    if metrics:
        print(f"[METRICS] Analyses performed: {len(metrics)}")
        avg_time = sum(m.total_time_ms for m in metrics) / len(metrics) if metrics else 0
        print(f"[METRICS] Average analysis time: {avg_time:.1f}ms")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    
    print("[NEXT] Next steps:")
    print("1. Run: python main.py --position 'Data Scientist'")
    print("2. Run: python main.py --skills 'Python,SQL' --positions 'Data Scientist,Python Developer'")
    print("3. Run: python main.py --metrics")
    print("4. Check README.md for full documentation")


if __name__ == "__main__":
    demo_complete_workflow()
