# routers/agent1_router.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agent1.agent1 import run_agent1

router = APIRouter(prefix="/agent1", tags=["Agent 1 - Course Outline"])

class Agent1Request(BaseModel):
    instructor_prompt: str
    level: str = "beginner"
    modules: int = 6

@router.post("/generate")
async def generate_outline(req: Agent1Request):
    try:
        title, outline = run_agent1(req.instructor_prompt, req.level, req.modules)
        return {"course_title": title, "modules": outline}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
