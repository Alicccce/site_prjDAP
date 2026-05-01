import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict

from models import SkillsPosition, Skill, SkillImportance, JobMatch, User


class AIAssistant:
    """
    AI-ассистент для анализа вакансий и сравнения навыков
    Разработала в рамках курсовой работы по анализу данных
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyzeVacancies(self, vacancies_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Анализ вакансий и извлечение навыков
        
        Args:
            vacancies_data: Список вакансий от hh.ru
            
        Returns:
            Dict: Результаты анализа в нужном формате
        """
        if not vacancies_data:
            self.logger.warning("Нет вакансий для анализа")
            return {
                "error": "Нет вакансий для анализа",
                "skills": [],
                "total_vacancies": 0
            }
        
        try:
            # Извлекаем навыки из всех вакансий
            skill_analysis = self._extract_skills_from_vacancies(vacancies_data)
            
            # Форматируем результат как ожидает VacancyAnalysisService
            result = {
                "skills": [
                    {
                        "name": skill["name"],
                        "frequency": skill["frequency"],
                        "importance": skill["importance"].value,
                        "count": skill["count"]
                    }
                    for skill in skill_analysis["skills"]
                ],
                "total_vacancies": skill_analysis["total_vacancies"],
                "analysis_summary": {
                    "mandatory_skills": len([s for s in skill_analysis["skills"] 
                                           if s["importance"] == SkillImportance.MANDATORY]),
                    "recommended_skills": len([s for s in skill_analysis["skills"] 
                                              if s["importance"] == SkillImportance.RECOMMENDED]),
                    "optional_skills": len([s for s in skill_analysis["skills"] 
                                           if s["importance"] == SkillImportance.OPTIONAL])
                }
            }
            
            self.logger.info(f"Успешно проанализировано {len(vacancies_data)} вакансий, "
                           f"найдено {len(result['skills'])} навыков")
            
            return result
            
        except Exception as e:
            error_msg = f"Ошибка при анализе вакансий: {str(e)}"
            self.logger.error(error_msg)
            return {
                "error": error_msg,
                "skills": [],
                "total_vacancies": len(vacancies_data)
            }
    
    def _extract_skills_from_vacancies(self, vacancies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Извлекает навыки из вакансий и анализирует частоту"""
        from collections import Counter
        
        # Словарь навыков (такой же как в VacancyAnalysisService)
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
        
        skills_lower = {skill.lower(): skill for skill in SKILLS}
        skill_counter = Counter()
        total_vacancies = len(vacancies)
        
        for vacancy in vacancies:
            # Собираем текст из разных полей вакансии
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
            
            # Извлекаем навыки из этой вакансии
            found_skills = self._extract_skills_from_text(full_text, skills_lower)
            
            # Считаем каждый навык один раз на вакансию
            for skill in set(found_skills):
                skill_counter[skill] += 1
        
        # Преобразуем в данные навыков с уровнями важности
        skills_data = []
        for skill_name, count in skill_counter.most_common():
            frequency = (count / total_vacancies) * 100
            
            # Определяем важность по частоте
            if frequency >= 70:
                importance = SkillImportance.MANDATORY
            elif frequency >= 40:
                importance = SkillImportance.RECOMMENDED
            else:
                importance = SkillImportance.OPTIONAL
            
            skills_data.append({
                "name": skill_name,
                "importance": importance,
                "frequency": round(frequency, 1),
                "count": count
            })
        
        return {
            "skills": skills_data,
            "total_vacancies": total_vacancies
        }
    
    def _extract_skills_from_text(self, text: str, skills_lower: Dict[str, str]) -> List[str]:
        """Extract skills from text using case-insensitive matching"""
        if not text:
            return []
        
        text = text.lower()
        found = set()
        
        for skill_key, skill_name in skills_lower.items():
            if skill_key in text:
                found.add(skill_name)
        
        return list(found)
    
    def matchUserSkillsWithJobs(self, user_skills: List[str], job_analyses: List[SkillsPosition]) -> List[JobMatch]:
        """
        Compare user skills with job requirements and calculate match percentage
        
        Args:
            user_skills: List of user's skills (e.g., ["Python", "SQL"])
            job_analyses: List of SkillsPosition objects with job requirements
            
        Returns:
            List of JobMatch objects sorted by match percentage
        """
        if not user_skills:
            self.logger.warning("User has no skills to match")
            return []
        
        if not job_analyses:
            self.logger.warning("No job analyses provided for matching")
            return []
        
        # Normalize user skills to lowercase for comparison
        user_skills_lower = {skill.lower() for skill in user_skills}
        matches = []
        
        for job_analysis in job_analyses:
            match_result = self._calculate_job_match(user_skills_lower, job_analysis)
            if match_result:
                matches.append(match_result)
        
        # Sort by match percentage (highest first)
        matches.sort(key=lambda x: x.match_percentage, reverse=True)
        
        self.logger.info(f"Generated {len(matches)} job matches for user with {len(user_skills)} skills")
        
        return matches
    
    def _calculate_job_match(self, user_skills_lower: set, job_analysis: SkillsPosition) -> Optional[JobMatch]:
        """Calculate match percentage for a single job"""
        if not job_analysis.skills:
            return None
        
        # Separate skills by importance
        mandatory_skills = []
        recommended_skills = []
        optional_skills = []
        
        for skill in job_analysis.skills:
            if skill.importance == SkillImportance.MANDATORY:
                mandatory_skills.append(skill.name.lower())
            elif skill.importance == SkillImportance.RECOMMENDED:
                recommended_skills.append(skill.name.lower())
            else:
                optional_skills.append(skill.name.lower())
        
        # Calculate matches
        matched_mandatory = []
        matched_recommended = []
        matched_optional = []
        
        all_job_skills_lower = set()
        
        # Check mandatory skills
        for skill in mandatory_skills:
            all_job_skills_lower.add(skill)
            if skill in user_skills_lower:
                matched_mandatory.append(skill.title())
        
        # Check recommended skills
        for skill in recommended_skills:
            all_job_skills_lower.add(skill)
            if skill in user_skills_lower:
                matched_recommended.append(skill.title())
        
        # Check optional skills
        for skill in optional_skills:
            all_job_skills_lower.add(skill)
            if skill in user_skills_lower:
                matched_optional.append(skill.title())
        
        # Calculate percentages using weighted formula
        # Mandatory skills: 70% weight, Recommended: 20% weight, Optional: 10% weight
        total_weight = 0
        matched_weight = 0
        
        if mandatory_skills:
            mandatory_percentage = len(matched_mandatory) / len(mandatory_skills)
            matched_weight += mandatory_percentage * 0.7
            total_weight += 0.7
        
        if recommended_skills:
            recommended_percentage = len(matched_recommended) / len(recommended_skills)
            matched_weight += recommended_percentage * 0.2
            total_weight += 0.2
        
        if optional_skills:
            optional_percentage = len(matched_optional) / len(optional_skills)
            matched_weight += optional_percentage * 0.1
            total_weight += 0.1
        
        # If no skills defined for this job, skip it
        if total_weight == 0:
            return None
        
        # Normalize to 100% scale
        match_percentage = (matched_weight / total_weight) * 100
        
        # Find missing skills
        all_matched_skills = set(matched_mandatory + matched_recommended + matched_optional)
        missing_skills = [skill.title() for skill in all_job_skills_lower 
                         if skill not in user_skills_lower]
        
        missing_mandatory = [skill.title() for skill in mandatory_skills 
                           if skill not in user_skills_lower]
        
        # Create JobMatch object
        job_match = JobMatch(
            job_title=job_analysis.position_name,
            match_percentage=round(match_percentage, 1),
            matched_skills=list(all_matched_skills),
            missing_skills=missing_skills,
            missing_mandatory=missing_mandatory,
            position_id=job_analysis.id
        )
        
        return job_match
    
    def getSkillRecommendations(self, user_skills: List[str], job_analyses: List[SkillsPosition], 
                               limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get skill recommendations based on job analyses
        
        Args:
            user_skills: User's current skills
            job_analyses: List of job analyses
            limit: Maximum number of recommendations
            
        Returns:
            List of recommended skills with frequency and importance
        """
        user_skills_lower = {skill.lower() for skill in user_skills}
        skill_frequency = defaultdict(list)
        
        # Collect all skills from job analyses
        for job_analysis in job_analyses:
            for skill in job_analysis.skills:
                if skill.name.lower() not in user_skills_lower:
                    skill_frequency[skill.name.lower()].append({
                        'frequency': skill.frequency,
                        'importance': skill.importance,
                        'job_title': job_analysis.position_name
                    })
        
        # Calculate recommendation score
        recommendations = []
        for skill_name, occurrences in skill_frequency.items():
            if not occurrences:
                continue
            
            # Calculate average frequency and max importance
            avg_frequency = sum(occ['frequency'] for occ in occurrences) / len(occurrences)
            max_importance = max(occ['importance'].value for occ in occurrences)
            job_count = len(set(occ['job_title'] for occ in occurrences))
            
            # Calculate recommendation score
            score = avg_frequency * job_count
            
            recommendations.append({
                'name': skill_name.title(),
                'frequency': round(avg_frequency, 1),
                'importance': max_importance,
                'job_count': job_count,
                'score': round(score, 1)
            })
        
        # Sort by score and return top recommendations
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return recommendations[:limit]
