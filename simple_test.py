#!/usr/bin/env python3
"""
Simple test to verify core functionality without external dependencies
"""

from models import SkillsPosition, Skill, SkillImportance, User, JobMatch
from ai_assistant import AIAssistant


def test_ai_functionality():
    """Test AI assistant functionality with sample data"""
    print("Testing AI Assistant functionality...")
    
    ai = AIAssistant()
    
    # Test vacancy analysis
    sample_vacancies = [
        {
            "name": "Data Scientist",
            "description": "Looking for Data Scientist with Python, Machine Learning, and SQL skills",
            "snippet": {"requirement": "Python, Machine Learning, SQL"}
        },
        {
            "name": "Python Developer", 
            "description": "Python developer needed with Django and PostgreSQL",
            "snippet": {"requirement": "Python, Django, PostgreSQL"}
        }
    ]
    
    result = ai.analyzeVacancies(sample_vacancies)
    
    print(f"Analysis result:")
    print(f"- Total vacancies: {result.get('total_vacancies', 0)}")
    print(f"- Skills found: {len(result.get('skills', []))}")
    
    for skill in result.get('skills', [])[:5]:
        print(f"  * {skill['name']}: {skill['frequency']}% ({skill['importance']})")
    
    # Test skill matching
    job_analyses = [
        SkillsPosition(
            position_name="Data Scientist",
            skills=[
                Skill("Python", SkillImportance.MANDATORY, 100),
                Skill("Machine Learning", SkillImportance.MANDATORY, 50),
                Skill("SQL", SkillImportance.RECOMMENDED, 50)
            ]
        )
    ]
    
    user_skills = ["Python", "SQL", "Docker"]
    matches = ai.matchUserSkillsWithJobs(user_skills, job_analyses)
    
    print(f"\nSkill matching results:")
    for match in matches:
        print(f"- {match.job_title}: {match.match_percentage}%")
        print(f"  Matched: {', '.join(match.matched_skills)}")
        print(f"  Missing: {', '.join(match.missing_skills)}")
    
    # Test recommendations
    recommendations = ai.getSkillRecommendations(user_skills, job_analyses)
    
    print(f"\nSkill recommendations:")
    for rec in recommendations[:3]:
        print(f"- {rec['name']}: {rec['frequency']}% (score: {rec['score']})")
    
    print("\nAll tests completed successfully!")


if __name__ == "__main__":
    test_ai_functionality()
