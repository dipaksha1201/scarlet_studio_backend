# routers/agent3_router.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict
from agent3.agent3 import run_agent3

router = APIRouter(prefix="/agent3", tags=["Agent 3 – Assessments"])

class ModuleAssessmentRequest(BaseModel):
    title: str
    description: str
    type: str = Field(..., description="Type of assessment: mcq, qa, or flashcards")

class Agent3Request(BaseModel):
    assessments: List[ModuleAssessmentRequest]

class Agent3Response(BaseModel):
    assessment: List[Dict[str, str]]

@router.post("/generate", response_model=Agent3Response)
async def generate_assessment(req: Agent3Request):
    try:
        assessment = run_agent3([a.dict() for a in req.assessments])
        return {"assessment": assessment}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
