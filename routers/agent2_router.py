# routers/agent2_router.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict
from agent2.agent2 import run_agent2

router = APIRouter(prefix="/agent2", tags=["Agent 2 – Descriptions"])

class Agent2Request(BaseModel):
    modules: List[str] = Field(..., example=[
        "Introduction to AI",
        "Machine Learning Basics",
        "Neural Networks"
    ])

class Agent2Response(BaseModel):
    descriptions: List[Dict[str, str]]

@router.post("/describe", response_model=Agent2Response)
async def generate_descriptions(req: Agent2Request):
    try:
        descriptions = run_agent2(req.modules)
        return {"descriptions": descriptions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
