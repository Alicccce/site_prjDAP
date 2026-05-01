#!/usr/bin/env python3
"""
Основное приложение для демонстрации системы анализа вакансий

Разработала как курсовую работу по анализу данных

Usage:
    python main.py --position "Data Scientist"
    python main.py --skills "Python,SQL" --positions "Data Scientist,Python Developer"
    python main.py --test  # Запуск тестов
"""

import argparse
import json
import sys
from datetime import datetime
from typing import List

from models import User, SkillsPosition, JobMatch
from vacancy_analysis_service import VacancyAnalysisService
from ai_assistant import AIAssistant
from test_integration import run_integration_tests


class VacancyAnalysisApp:
    """Основной класс приложения"""
    
    def __init__(self):
        # Инициализируем сервисы с настройками по умолчанию
        self.vacancy_service = VacancyAnalysisService(cache_duration_hours=1, max_vacancies=50)
        self.ai_assistant = AIAssistant()
    
    def analyze_position(self, position_name: str, area: int = 1) -> SkillsPosition:
        """Анализ должности и возврат данных о навыках"""
        print(f"\n[АНАЛИЗ] Анализируем должность: {position_name}")
        print("-" * 50)
        
        try:
            result = self.vacancy_service.analyze_position(position_name, area)
            
            # Показываем результаты
            print(f"[ГОТОВО] Анализ завершен!")
            print(f"[СТАТИСТИКА] Проанализировано вакансий: {result.total_vacancies_analyzed}")
            print(f"[СТАТИСТИКА] Найдено навыков: {len(result.skills)}")
            
            if result.skills:
                print(f"\n[ТОП НАВЫКИ] Топ навыков по частоте:")
                for i, skill in enumerate(result.skills[:10], 1):
                    importance_icon = self._get_importance_icon(skill.importance.value)
                    print(f"  {i:2}. {skill.name:<20} {skill.frequency:5.1f}% {importance_icon}")
            
            return result
            
        except Exception as e:
            print(f"[ОШИБКА] Ошибка при анализе должности: {e}")
            raise
    
    def match_user_skills(self, user_skills: List[str], positions: List[str]) -> List[JobMatch]:
        """Match user skills with job positions"""
        print(f"\n👤 User skills: {', '.join(user_skills)}")
        print(f"🎯 Analyzing positions: {', '.join(positions)}")
        print("-" * 50)
        
        # Analyze all positions
        job_analyses = []
        for position in positions:
            try:
                analysis = self.analyze_position(position)
                job_analyses.append(analysis)
            except Exception as e:
                print(f"⚠️  Could not analyze {position}: {e}")
                continue
        
        if not job_analyses:
            print("❌ No successful job analyses to match against")
            return []
        
        # Match skills
        matches = self.ai_assistant.matchUserSkillsWithJobs(user_skills, job_analyses)
        
        # Display matches
        if matches:
            print(f"\n🎯 Skill matching results ({len(matches)} matches):")
            print("-" * 50)
            
            for i, match in enumerate(matches, 1):
                match_icon = self._get_match_icon(match.match_percentage)
                print(f"{i}. {match.job_title:<20} {match.match_percentage:5.1f}% {match_icon}")
                
                if match.matched_skills:
                    print(f"   ✅ Matched: {', '.join(match.matched_skills[:5])}")
                
                if match.missing_mandatory:
                    print(f"   ❌ Missing mandatory: {', '.join(match.missing_mandatory)}")
                elif match.missing_skills:
                    missing = match.missing_skills[:3]
                    print(f"   ⚠️  Missing: {', '.join(missing)}")
                
                print()
        else:
            print("❌ No matches found")
        
        return matches
    
    def get_skill_recommendations(self, user_skills: List[str], positions: List[str], limit: int = 10):
        """Get skill recommendations for improvement"""
        print(f"\n💡 Getting skill recommendations...")
        print("-" * 50)
        
        # Analyze positions
        job_analyses = []
        for position in positions:
            try:
                analysis = self.analyze_position(position)
                job_analyses.append(analysis)
            except Exception as e:
                print(f"⚠️  Could not analyze {position}: {e}")
                continue
        
        if not job_analyses:
            print("❌ No successful job analyses for recommendations")
            return []
        
        # Get recommendations
        recommendations = self.ai_assistant.getSkillRecommendations(user_skills, job_analyses, limit)
        
        if recommendations:
            print(f"\n💡 Top {len(recommendations)} skill recommendations:")
            print("-" * 50)
            
            for i, rec in enumerate(recommendations, 1):
                importance_icon = self._get_importance_icon(rec['importance'])
                print(f"{i}. {rec['name']:<20} {rec['frequency']:5.1f}% {importance_icon}")
                print(f"   📈 Appears in {rec['job_count']} positions, score: {rec['score']}")
                print()
        else:
            print("✅ You already have all the recommended skills!")
        
        return recommendations
    
    def show_metrics(self):
        """Show performance metrics"""
        metrics = self.vacancy_service.get_metrics()
        
        if not metrics:
            print("📊 No metrics available yet")
            return
        
        print(f"\n📊 Performance Metrics ({len(metrics)} analyses):")
        print("-" * 50)
        
        total_time = sum(m.total_time_ms for m in metrics)
        avg_time = total_time / len(metrics)
        
        print(f"⏱️  Average analysis time: {avg_time:.1f}ms")
        print(f"🔍 Total vacancies processed: {sum(m.vacancies_analyzed for m in metrics)}")
        print(f"🎯 Total skills extracted: {sum(m.skills_extracted for m in metrics)}")
        
        # Cache stats
        cache_stats = self.vacancy_service.get_cache_stats()
        print(f"💾 Cache entries: {cache_stats['active_entries']}/{cache_stats['total_entries']}")
    
    def _get_importance_icon(self, importance: str) -> str:
        """Get icon for skill importance"""
        icons = {
            "mandatory": "🔥",
            "recommended": "⭐", 
            "optional": "💡"
        }
        return icons.get(importance, "❓")
    
    def _get_match_icon(self, percentage: float) -> str:
        """Get icon for match percentage"""
        if percentage >= 80:
            return "🎯"
        elif percentage >= 60:
            return "✅"
        elif percentage >= 40:
            return "⚠️"
        else:
            return "❌"


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="AI-Integrated Vacancy Analysis System")
    parser.add_argument("--position", type=str, help="Job position to analyze")
    parser.add_argument("--skills", type=str, help="Comma-separated list of user skills")
    parser.add_argument("--positions", type=str, help="Comma-separated list of positions to match against")
    parser.add_argument("--area", type=int, default=1, help="Area ID (1=Moscow, 2=St. Petersburg)")
    parser.add_argument("--recommendations", action="store_true", help="Show skill recommendations")
    parser.add_argument("--metrics", action="store_true", help="Show performance metrics")
    parser.add_argument("--test", action="store_true", help="Run integration tests")
    parser.add_argument("--clear-cache", action="store_true", help="Clear analysis cache")
    
    args = parser.parse_args()
    
    app = VacancyAnalysisApp()
    
    # Handle special commands
    if args.test:
        success = run_integration_tests()
        sys.exit(0 if success else 1)
    
    if args.clear_cache:
        app.vacancy_service.clear_cache()
        print("✅ Cache cleared")
        return
    
    if args.metrics:
        app.show_metrics()
        return
    
    # Main functionality
    if args.position:
        # Analyze single position
        try:
            result = app.analyze_position(args.position, args.area)
            
            # Save result to file
            output_file = f"analysis_{args.position.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Convert to serializable format
            result_data = {
                "position_name": result.position_name,
                "search_query": result.search_query,
                "total_vacancies_analyzed": result.total_vacancies_analyzed,
                "created_at": result.created_at.isoformat(),
                "skills": [
                    {
                        "name": skill.name,
                        "importance": skill.importance.value,
                        "frequency": skill.frequency
                    }
                    for skill in result.skills
                ]
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Results saved to: {output_file}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
    
    elif args.skills and args.positions:
        # Match user skills with positions
        user_skills = [skill.strip() for skill in args.skills.split(',')]
        positions = [pos.strip() for pos in args.positions.split(',')]
        
        matches = app.match_user_skills(user_skills, positions)
        
        if args.recommendations:
            app.get_skill_recommendations(user_skills, positions)
    
    else:
        # Show help
        print("🤖 AI-Integrated Vacancy Analysis System")
        print("=" * 50)
        print("\nUsage examples:")
        print("  python main.py --position 'Data Scientist'")
        print("  python main.py --skills 'Python,SQL' --positions 'Data Scientist,Python Developer'")
        print("  python main.py --test")
        print("  python main.py --metrics")
        print("  python main.py --clear-cache")
        print("\nUse --help for more options")


if __name__ == "__main__":
    main()
