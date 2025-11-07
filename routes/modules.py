from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import json
from pathlib import Path
from ..auth.api_key import get_api_key

router = APIRouter(prefix="/modules", tags=["modules"])

DATA_PATH = Path(__file__).parents[1] / "data" / "static_modules.json"

class ModuleIn(BaseModel):
    id: str
    title: str
    paragraphs: List[str]
    meta: Dict = {}

class ModuleOut(BaseModel):
    id: str
    title: str
    meta: Dict = {}

def _load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_data(obj):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)

@router.get("", response_model=List[ModuleOut], dependencies=[Depends(get_api_key)])
def list_modules():
    data = _load_data()
    return [ {"id": m["id"], "title": m["title"], "meta": m.get("meta", {})} for m in data.get("modules", []) ]

@router.post("", response_model=ModuleOut, dependencies=[Depends(get_api_key)])
def create_module(module: ModuleIn):
    data = _load_data()
    exists = next((m for m in data.get("modules", []) if m["id"] == module.id), None)
    if exists:
        raise HTTPException(status_code=400, detail="Module id already exists")
    data["modules"].append(module.dict())
    _save_data(data)
    return {"id": module.id, "title": module.title, "meta": module.meta}

