# routers/pipeline_router.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from agent1.agent1 import run_agent1
from agent2.agent2 import run_agent2
from agent3.agent3 import run_agent3

router = APIRouter(prefix="/pipeline", tags=["Full Pipeline"])

class PipelineRequest(BaseModel):
    instructor_prompt: str = Field(..., example="Introduction to AI")
    level: str = Field(..., example="beginner")
    modules: int = Field(..., example=4)
    assessment_preferences: Optional[List[str]] = Field(
        None,
        example=["mcq", "flashcards", "qa", "mcq"],
        description="Assessment type for each module"
    )

class PipelineResponse(BaseModel):
    course_title: str
    modules: List[str]
    descriptions: List[Dict[str, str]]
    assessments: List[Dict[str, Any]]

@router.post("/run", response_model=PipelineResponse)
async def run_full_pipeline(req: PipelineRequest):
    try:
        course_title, outline = run_agent1(req.instructor_prompt, req.level, req.modules)
        descriptions = run_agent2(outline)

        preferences = req.assessment_preferences or ["mcq"] * len(descriptions)
        assessments_input = [
            {
                "title": d["title"],
                "description": d["description"],
                "type": preferences[i] if i < len(preferences) else "mcq",
            }
            for i, d in enumerate(descriptions)
        ]

        assessments = run_agent3(assessments_input)
        print("✅ Agent 3 OK. Generated", len(assessments), "modules")

        return {
            "course_title": course_title,
            "modules": outline,
            "descriptions": descriptions,
            "assessments": assessments,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
