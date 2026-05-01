# -*- coding: utf-8 -*-
# main.py
import colorama
from colorama import init, Fore, Style
# Инициализация colorama (автоматически настраивает кодировку)
init(autoreset=True)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from services.user_skill_service import UserSkillService
from services.vacancy_analysis_service import VacancyAnalysisService

# создаём приложение FastAPI
app = FastAPI(
    title="Vacancy Analysis API",
    description="API for analyzing vacancies and managing user skills",
    version="1.0.0"
)

# инициализируем сервисы
user_skill_service = UserSkillService()
analysis_service = VacancyAnalysisService()


# модели запроса/ответа 

class SaveUserSkillsRequest(BaseModel):
    """Request model for POST /api/user/skills/session"""
    session_id: int
    skill_ids: List[int]


class SaveUserSkillsResponse(BaseModel):
    """Response model for POST /api/user/skills/session"""
    success: bool
    message: str
    deleted_count: int
    saved_skills: List[dict]


class SkillResponse(BaseModel):
    """Skill info response"""
    record_id: int
    skill_id: int
    skill_name: str
    specified_date: str


class AnalyzeByPositionRequest(BaseModel):
    """Request model for POST /api/analyze/by-position"""
    query: str


class AnalyzeByPositionResponse(BaseModel):
    """Response model for POST /api/analyze/by-position"""
    skills: List[dict]
    message: str


# апи эндпоинты

@app.post("/api/user/skills/session", response_model=SaveUserSkillsResponse)
async def save_user_skills(request: SaveUserSkillsRequest, user_id: int = 1):
    """
    Save user's selected skills for a specific session.
    Replaces all previous selections for this session.
    
    - **session_id**: ID of the search session
    - **skill_ids**: List of skill IDs that user selected
    
    Returns saved skills count and details.
    """
    try:
        result = user_skill_service.save_user_skills_for_session(
            user_id=user_id,
            session_id=request.session_id,
            skill_ids=request.skill_ids
        )
        return SaveUserSkillsResponse(**result)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/user/skills/session")
async def get_user_skills(session_id: int, user_id: int = 1):
    """
    Get user's selected skills for a specific session.
    
    - **session_id**: ID of the search session
    - **user_id**: ID of the user (default 1 for testing)
    
    Returns list of skills with details.
    """
    try:
        skills = user_skill_service.get_user_skills_for_session(
            user_id=user_id,
            session_id=session_id
        )
        
        # конвертирует datetime в string для JSON
        for skill in skills:
            if 'specified_date' in skill and skill['specified_date']:
                skill['specified_date'] = str(skill['specified_date'])
        
        return {
            "success": True,
            "session_id": session_id,
            "skills": skills,
            "count": len(skills)
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/analyze/by-position", response_model=AnalyzeByPositionResponse)
async def analyze_by_position(request: AnalyzeByPositionRequest, user_id: int = 1):
    """
    Analyze vacancies by position and save results.
    
    - **query**: Position name to search for (e.g., "Data Scientist")
    - **user_id**: ID of the user (default 1 for testing)
    
    Returns list of extracted skills.
    """
    try:
        skills = analysis_service.analyzeByPosition(
            user_id=user_id,
            position_query=request.query
        )
        
        return AnalyzeByPositionResponse(
            skills=skills,
            message=f"Analysis complete. Found {len(skills)} skills."
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=f"hh.ru timeout: {str(e)}")
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Connection error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
