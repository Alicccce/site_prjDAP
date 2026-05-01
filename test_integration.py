import json
import unittest
from datetime import datetime
from typing import Dict, List, Any

from models import SkillsPosition, Skill, SkillImportance, User, JobMatch
from vacancy_analysis_service import VacancyAnalysisService
from ai_assistant import AIAssistant


class TestIntegration(unittest.TestCase):
    """Integration tests for the vacancy analysis system"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data and services"""
        cls.ai_assistant = AIAssistant()
        cls.vacancy_service = VacancyAnalysisService(cache_duration_hours=24, max_vacancies=10)
        
        # Sample hh.ru vacancy data (saved from real API response)
        cls.sample_vacancies = [
            {
                "id": "1",
                "name": "Data Scientist",
                "description": "Мы ищем Data Scientist с опытом работы с Python, машинным обучением и статистикой. Требуется знание SQL, опыт работы с большими данными.",
                "snippet": {
                    "requirement": "Python, Machine Learning, SQL, Статистика",
                    "responsibility": "Анализ данных, построение моделей ML"
                },
                "employer": {"name": "Tech Company"},
                "area": {"name": "Москва"}
            },
            {
                "id": "2", 
                "name": "Python Developer",
                "description": "Ищем Python разработчика. Знание Django, PostgreSQL, Docker. Опыт работы с REST API обязательное требование.",
                "snippet": {
                    "requirement": "Python, Django, PostgreSQL, Docker, REST API",
                    "responsibility": "Разработка веб-приложений"
                },
                "employer": {"name": "Startup"},
                "area": {"name": "Санкт-Петербург"}
            },
            {
                "id": "3",
                "name": "ML Engineer",
                "description": "Machine Learning Engineer с опытом в TensorFlow, PyTorch. Требуется знание Python, Scikit-learn, Pandas.",
                "snippet": {
                    "requirement": "Python, TensorFlow, PyTorch, Scikit-learn, Pandas",
                    "responsibility": "Разработка ML моделей"
                },
                "employer": {"name": "AI Lab"},
                "area": {"name": "Москва"}
            },
            {
                "id": "4",
                "name": "Data Analyst",
                "description": "Аналитик данных с опытом SQL, Excel, Tableau. Знание Python приветствуется.",
                "snippet": {
                    "requirement": "SQL, Excel, Tableau",
                    "responsibility": "Анализ бизнес-данных"
                },
                "employer": {"name": "Bank"},
                "area": {"name": "Москва"}
            },
            {
                "id": "5",
                "name": "Full Stack Developer",
                "description": "Full Stack разработчик. Требуется JavaScript, React, Node.js, MongoDB. Знание Docker и Kubernetes плюсом.",
                "snippet": {
                    "requirement": "JavaScript, React, Node.js, MongoDB",
                    "responsibility": "Разработка full-stack приложений"
                },
                "employer": {"name": "Web Agency"},
                "area": {"name": "Санкт-Петербург"}
            }
        ]
        
        # Save sample data to file for testing
        with open('test_vacancies.json', 'w', encoding='utf-8') as f:
            json.dump(cls.sample_vacancies, f, ensure_ascii=False, indent=2)
    
    def test_ai_analyze_vacancies(self):
        """Test AI analysis of vacancies"""
        result = self.ai_assistant.analyzeVacancies(self.sample_vacancies)
        
        # Check structure
        self.assertIn('skills', result)
        self.assertIn('total_vacancies', result)
        self.assertEqual(result['total_vacancies'], 5)
        
        # Check that skills were extracted
        skills = result['skills']
        self.assertGreater(len(skills), 0)
        
        # Check skill structure
        for skill in skills:
            self.assertIn('name', skill)
            self.assertIn('frequency', skill)
            self.assertIn('importance', skill)
            self.assertIn('count', skill)
        
        # Check that Python is detected (should be in multiple vacancies)
        python_skills = [s for s in skills if s['name'] == 'Python']
        self.assertGreater(len(python_skills), 0)
        self.assertGreater(python_skills[0]['frequency'], 0)
        
        print(f"+ AI Analysis: Found {len(skills)} skills from {result['total_vacancies']} vacancies")
    
    def test_vacancy_service_analyze_position(self):
        """Test VacancyAnalysisService with mock data"""
        # Mock the fetch_vacancies to return our sample data
        def mock_fetch_vacancies(query, area=1, per_page=20):
            return {
                'items': self.sample_vacancies[:per_page],
                'found': len(self.sample_vacancies)
            }
        
        # Replace the fetch_vacancies method temporarily
        import hh_parser.parse_vacancies
        original_fetch = hh_parser.parse_vacancies.fetch_vacancies
        hh_parser.parse_vacancies.fetch_vacancies = mock_fetch_vacancies
        
        try:
            # Test analysis
            result = self.vacancy_service.analyze_position("Data Scientist")
            
            # Check result structure
            self.assertIsInstance(result, SkillsPosition)
            self.assertEqual(result.position_name, "Data Scientist")
            self.assertEqual(result.total_vacancies_analyzed, len(self.sample_vacancies))
            self.assertGreater(len(result.skills), 0)
            
            # Check skills structure
            for skill in result.skills:
                self.assertIsInstance(skill, Skill)
                self.assertIsInstance(skill.importance, SkillImportance)
                self.assertGreaterEqual(skill.frequency, 0)
                self.assertLessEqual(skill.frequency, 100)
            
            print(f"+ Vacancy Service: Analyzed position '{result.position_name}' "
                  f"with {len(result.skills)} skills")
            
        finally:
            # Restore original method
            hh_parser.parse_vacancies.fetch_vacancies = original_fetch
    
    def test_skill_matching(self):
        """Test user skills matching with job analyses"""
        # Create sample job analyses
        job_analyses = [
            SkillsPosition(
                position_name="Data Scientist",
                skills=[
                    Skill("Python", SkillImportance.MANDATORY, 80),
                    Skill("Machine Learning", SkillImportance.MANDATORY, 60),
                    Skill("SQL", SkillImportance.RECOMMENDED, 70),
                    Skill("Statistics", SkillImportance.RECOMMENDED, 50)
                ],
                total_vacancies_analyzed=10
            ),
            SkillsPosition(
                position_name="Python Developer",
                skills=[
                    Skill("Python", SkillImportance.MANDATORY, 100),
                    Skill("Django", SkillImportance.RECOMMENDED, 60),
                    Skill("PostgreSQL", SkillImportance.RECOMMENDED, 50),
                    Skill("Docker", SkillImportance.OPTIONAL, 30)
                ],
                total_vacancies_analyzed=8
            ),
            SkillsPosition(
                position_name="Full Stack Developer",
                skills=[
                    Skill("JavaScript", SkillImportance.MANDATORY, 90),
                    Skill("React", SkillImportance.MANDATORY, 70),
                    Skill("Node.js", SkillImportance.RECOMMENDED, 60),
                    Skill("MongoDB", SkillImportance.OPTIONAL, 40)
                ],
                total_vacancies_analyzed=5
            )
        ]
        
        # Test user with good match for Data Scientist
        user_skills = ["Python", "SQL", "Machine Learning", "Statistics"]
        matches = self.ai_assistant.matchUserSkillsWithJobs(user_skills, job_analyses)
        
        self.assertGreater(len(matches), 0)
        
        # Check that Data Scientist is top match
        self.assertEqual(matches[0].job_title, "Data Scientist")
        self.assertGreater(matches[0].match_percentage, 70)
        
        # Check match structure
        for match in matches:
            self.assertIsInstance(match, JobMatch)
            self.assertGreaterEqual(match.match_percentage, 0)
            self.assertLessEqual(match.match_percentage, 100)
            self.assertIsInstance(match.matched_skills, list)
            self.assertIsInstance(match.missing_skills, list)
            self.assertIsInstance(match.missing_mandatory, list)
        
        print(f"+ Skill Matching: Generated {len(matches)} matches for user with {len(user_skills)} skills")
        print(f"  Top match: {matches[0].job_title} ({matches[0].match_percentage}% match)")
    
    def test_skill_recommendations(self):
        """Test skill recommendations"""
        # Create sample job analyses
        job_analyses = [
            SkillsPosition(
                position_name="Data Scientist",
                skills=[
                    Skill("Python", SkillImportance.MANDATORY, 80),
                    Skill("Machine Learning", SkillImportance.MANDATORY, 60),
                    Skill("SQL", SkillImportance.RECOMMENDED, 70),
                    Skill("TensorFlow", SkillImportance.RECOMMENDED, 40)
                ],
                total_vacancies_analyzed=10
            ),
            SkillsPosition(
                position_name="ML Engineer",
                skills=[
                    Skill("Python", SkillImportance.MANDATORY, 90),
                    Skill("TensorFlow", SkillImportance.MANDATORY, 70),
                    Skill("PyTorch", SkillImportance.RECOMMENDED, 50),
                    Skill("Docker", SkillImportance.OPTIONAL, 30)
                ],
                total_vacancies_analyzed=8
            )
        ]
        
        # User with basic Python skills
        user_skills = ["Python"]
        recommendations = self.ai_assistant.getSkillRecommendations(user_skills, job_analyses, limit=5)
        
        self.assertGreater(len(recommendations), 0)
        
        # Check recommendation structure
        for rec in recommendations:
            self.assertIn('name', rec)
            self.assertIn('frequency', rec)
            self.assertIn('importance', rec)
            self.assertIn('job_count', rec)
            self.assertIn('score', rec)
        
        # TensorFlow should be recommended (appears in both jobs)
        tensorflow_recs = [r for r in recommendations if r['name'] == 'Tensorflow']
        self.assertGreater(len(tensorflow_recs), 0)
        
        print(f"+ Skill Recommendations: Generated {len(recommendations)} recommendations")
        print(f"  Top recommendation: {recommendations[0]['name']} (score: {recommendations[0]['score']})")
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        # Test empty vacancies
        result = self.ai_assistant.analyzeVacancies([])
        self.assertIn('error', result)
        self.assertEqual(result['total_vacancies'], 0)
        
        # Test empty user skills
        matches = self.ai_assistant.matchUserSkillsWithJobs([], [])
        self.assertEqual(len(matches), 0)
        
        # Test user skills with no job analyses
        matches = self.ai_assistant.matchUserSkillsWithJobs(["Python"], [])
        self.assertEqual(len(matches), 0)
        
        print("+ Edge Cases: All edge cases handled correctly")
    
    def test_cache_functionality(self):
        """Test caching mechanism"""
        # Clear cache first
        self.vacancy_service.clear_cache()
        
        # Mock fetch_vacancies
        call_count = 0
        def mock_fetch_vacancies(query, area=1, per_page=20):
            nonlocal call_count
            call_count += 1
            return {
                'items': self.sample_vacancies[:per_page],
                'found': len(self.sample_vacancies)
            }
        
        import hh_parser.parse_vacancies
        original_fetch = hh_parser.parse_vacancies.fetch_vacancies
        hh_parser.parse_vacancies.fetch_vacancies = mock_fetch_vacancies
        
        try:
            # First call should hit API
            result1 = self.vacancy_service.analyze_position("Data Scientist")
            self.assertEqual(call_count, 1)
            
            # Second call should use cache
            result2 = self.vacancy_service.analyze_position("Data Scientist")
            self.assertEqual(call_count, 1)  # Should not increase
            
            # Results should be identical
            self.assertEqual(result1.position_name, result2.position_name)
            self.assertEqual(len(result1.skills), len(result2.skills))
            
            # Check cache stats
            stats = self.vacancy_service.get_cache_stats()
            self.assertEqual(stats['total_entries'], 1)
            self.assertEqual(stats['active_entries'], 1)
            
            print(f"+ Cache: Working correctly (1 API call for 2 requests)")
            
        finally:
            hh_parser.parse_vacancies.fetch_vacancies = original_fetch
    
    def test_metrics_collection(self):
        """Test metrics collection"""
        # Clear existing metrics
        self.vacancy_service.metrics.clear()
        
        # Mock fetch_vacancies
        def mock_fetch_vacancies(query, area=1, per_page=20):
            return {
                'items': self.sample_vacancies[:per_page],
                'found': len(self.sample_vacancies)
            }
        
        import hh_parser.parse_vacancies
        original_fetch = hh_parser.parse_vacancies.fetch_vacancies
        hh_parser.parse_vacancies.fetch_vacancies = mock_fetch_vacancies
        
        try:
            # Perform analysis
            self.vacancy_service.analyze_position("Data Scientist")
            
            # Check metrics
            metrics = self.vacancy_service.get_metrics()
            self.assertEqual(len(metrics), 1)
            
            metric = metrics[0]
            self.assertEqual(metric.search_query, "Data Scientist")
            self.assertGreater(metric.total_time_ms, 0)
            self.assertGreater(metric.hh_parsing_time_ms, 0)
            self.assertGreater(metric.ai_analysis_time_ms, 0)
            self.assertEqual(metric.vacancies_analyzed, len(self.sample_vacancies))
            self.assertGreater(metric.skills_extracted, 0)
            
            print(f"+ Metrics: Collected successfully "
                  f"(total time: {metric.total_time_ms:.1f}ms, "
                  f"skills: {metric.skills_extracted})")
            
        finally:
            hh_parser.parse_vacancies.fetch_vacancies = original_fetch


def run_integration_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("RUNNING INTEGRATION TESTS")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestIntegration)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall: {'SUCCESS' if success else 'FAILED'}")
    print("=" * 60)
    
    return success


if __name__ == "__main__":
    run_integration_tests()
