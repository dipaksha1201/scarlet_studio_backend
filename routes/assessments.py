from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
from ..auth.api_key import get_api_key
from ..services.assessment_designer import AssessmentDesigner, _load_performance, _save_performance, PERF_PATH, DATA_DIR

router = APIRouter(prefix="/assessments", tags=["assessments"])

DATA_PATH = Path(__file__).parents[1] / "data" / "static_modules.json"

def _load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

class GenerateRequest(BaseModel):
    module_id: str
    type: str  # 'quiz' | 'flashcards' | 'qa'
    count: int = 3

class EvaluateItem(BaseModel):
    id: str
    selected_index: int

class EvaluateRequest(BaseModel):
    assessment: Dict[str, Any]
    answers: List[EvaluateItem]
    module_id: Optional[str] = None

@router.get("/modules/{module_id}/content", dependencies=[Depends(get_api_key)])
def get_module_content(module_id: str):
    data = _load_data()
    module = next((m for m in data.get("modules", []) if m["id"] == module_id), None)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return {"id": module["id"], "title": module["title"], "paragraphs": module.get("paragraphs", [])}

@router.post("/generate", dependencies=[Depends(get_api_key)])
def generate_assessment(req: GenerateRequest):
    data = _load_data()
    module = next((m for m in data.get("modules", []) if m["id"] == req.module_id), None)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    designer = AssessmentDesigner(module)
    if req.type == "quiz":
        return designer.generate_quiz(num_questions=req.count)
    if req.type == "flashcards":
        return designer.generate_flashcards(num_cards=req.count)
    if req.type in ("qa", "qa_pairs"):
        return designer.generate_qa_pairs(num_pairs=req.count)
    raise HTTPException(status_code=400, detail="Unknown assessment type")

@router.post("/evaluate", dependencies=[Depends(get_api_key)])
def evaluate_assessment(req: EvaluateRequest):
    assessment = req.assessment
    answers_map = {a.id: a.selected_index for a in req.answers}
    score = 0
    total = 0
    module_id = req.module_id

    if assessment.get("type") == "quiz":
        for q in assessment.get("questions", []):
            total += 1
            correct = q.get("correct_index", 0)
            sel = answers_map.get(q.get("id"))
            if sel is not None and sel == correct:
                score += 1
            # update performance if module_id and source_index present
            if module_id and q.get("source_index") is not None:
                perf = _load_performance()
                mod_perf = perf.get(module_id, {"items": []})
                items = mod_perf.get("items", [])
                idx = q["source_index"]
                # ensure item exists
                if idx >= len(items):
                    for _ in range(len(items), idx + 1):
                        items.append({"index": len(items), "attempts": 0, "correct": 0})
                item = items[idx]
                item["attempts"] = item.get("attempts", 0) + 1
                if sel is not None and sel == correct:
                    item["correct"] = item.get("correct", 0) + 1
                mod_perf["items"] = items
                perf[module_id] = mod_perf
                _save_performance(perf)
    else:
        # For flashcards/qa we don't evaluate correctness by index; we can still record attempts if module_id provided
        if module_id:
            perf = _load_performance()
            mod_perf = perf.get(module_id, {"items": []})
            items = mod_perf.get("items", [])
            # gather source indices from assessment (cards/pairs)
            collection = assessment.get("pairs") or assessment.get("cards") or []
            for it in collection:
                idx = it.get("source_index")
                if idx is None:
                    continue
                if idx >= len(items):
                    for _ in range(len(items), idx + 1):
                        items.append({"index": len(items), "attempts": 0, "correct": 0})
                items[idx]["attempts"] = items[idx].get("attempts", 0) + 1
            mod_perf["items"] = items
            perf[module_id] = mod_perf
            _save_performance(perf)

    return {"score": score, "total": total}
