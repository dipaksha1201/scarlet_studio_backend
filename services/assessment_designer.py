from typing import List, Dict, Optional
import hashlib
import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # loads .env if present

DATA_DIR = Path(__file__).parents[1] / "data"
PERF_PATH = DATA_DIR / "performance.json"

def _load_performance() -> Dict:
    if not PERF_PATH.exists():
        return {}
    try:
        with open(PERF_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_performance(obj: Dict):
    PERF_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PERF_PATH, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)

class DesignerBase:
    def __init__(self, module: Dict):
        self.module = module
        self.paragraphs: List[str] = module.get("paragraphs", [])
        self.module_id: str = module.get("id", "")
        self._perf = _load_performance().get(self.module_id, {"items": []})

    def _seed(self) -> int:
        return int(hashlib.sha1(self.module_id.encode()).hexdigest(), 16)

    def _ensure_perf_items(self):
        # ensure performance items are aligned with paragraphs
        items = self._perf.get("items", [])
        if len(items) < len(self.paragraphs):
            for idx in range(len(items), len(self.paragraphs)):
                items.append({"index": idx, "attempts": 0, "correct": 0})
        self._perf["items"] = items

    def _scores(self) -> List[float]:
        # lower score means weaker item (should be selected first)
        self._ensure_perf_items()
        scores = []
        for it in self._perf["items"]:
            attempts = it.get("attempts", 0)
            correct = it.get("correct", 0)
            rate = (correct / attempts) if attempts > 0 else 0.0
            scores.append(rate)
        return scores

    def _pick_indices(self, n: int) -> List[int]:
        if not self.paragraphs:
            return []
        scores = self._scores()
        # produce (index, score) list and sort ascending (weaker first)
        indexed = list(enumerate(scores))
        seed = self._seed()
        # tie-breaker deterministic using seed
        indexed.sort(key=lambda x: (x[1], (seed + x[0]) % 997))
        picks = [i for i, _ in indexed[:min(n, len(indexed))]]
        # if not enough (e.g., no perf entries), fallback deterministic pick
        if len(picks) < n:
            for i in range(n):
                if i not in picks:
                    picks.append((seed + i) % len(self.paragraphs))
            picks = picks[:n]
        return picks

    def _output_meta(self) -> Dict:
        return {"source": "openrouter" if os.getenv("OPENROUTER_API_KEY") else "local"}

class QuizDesigner(DesignerBase):
    def generate(self, num_questions: int = 3) -> Dict:
        picks = self._pick_indices(num_questions + 2)
        questions = []
        for qi in range(min(num_questions, len(picks))):
            correct_idx = picks[qi]
            correct = self.paragraphs[correct_idx]
            # distractors: next two picked indices that are not correct
            distractors = []
            for idx in picks:
                if idx != correct_idx and len(distractors) < 2:
                    distractors.append(self.paragraphs[idx])
            options = [correct] + distractors
            questions.append({
                "id": f"q{qi+1}",
                "question": f"Select the best summary of point #{qi+1}:",
                "options": options,
                "correct_index": 0,
                "source_index": correct_idx  # tie back to paragraph for evaluation
            })
        out = {"type": "quiz", "title": f"Quiz for {self.module.get('title')}", "questions": questions}
        out.update(self._output_meta())
        return out

class FlashcardDesigner(DesignerBase):
    def generate(self, num_cards: int = 5) -> Dict:
        picks = self._pick_indices(num_cards)
        cards = []
        for i, idx in enumerate(picks):
            sent = self.paragraphs[idx]
            front = sent.split(",")[0]
            cards.append({"id": f"f{i+1}", "front": front, "back": sent, "source_index": idx})
        out = {"type": "flashcards", "title": f"Flashcards for {self.module.get('title')}", "cards": cards}
        out.update(self._output_meta())
        return out

class QAPairDesigner(DesignerBase):
    def generate(self, num_pairs: int = 5) -> Dict:
        picks = self._pick_indices(num_pairs)
        pairs = []
        for i, idx in enumerate(picks):
            sent = self.paragraphs[idx]
            q = f"What does the following mean? (item {i+1})"
            a = sent
            pairs.append({"id": f"p{i+1}", "question": q, "answer": a, "source_index": idx})
        out = {"type": "qa_pairs", "title": f"Q&A for {self.module.get('title')}", "pairs": pairs}
        out.update(self._output_meta())
        return out

# Compatibility wrapper used by routes (preserves previous API)
class AssessmentDesigner:
    def __init__(self, module: Dict):
        self.module = module

    def generate_quiz(self, num_questions: int = 3) -> Dict:
        return QuizDesigner(self.module).generate(num_questions=num_questions)

    def generate_flashcards(self, num_cards: int = 5) -> Dict:
        return FlashcardDesigner(self.module).generate(num_cards=num_cards)

    def generate_qa_pairs(self, num_pairs: int = 5) -> Dict:
        return QAPairDesigner(self.module).generate(num_pairs=num_pairs)
