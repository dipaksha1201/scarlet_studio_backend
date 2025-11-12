# generation/module.py
import json
import re
from pydantic import BaseModel, Field, ValidationError, validator
from typing import List

class Quiz(BaseModel):
    question: str = Field(..., min_length=1)
    options: List[str]
    correct_option_index: int
    explanation: str = Field(..., min_length=1)

    @validator("options")
    def options_must_be_four_nonempty(cls, v):
        if not isinstance(v, list):
            raise ValueError("options must be a list of 4 strings")
        if len(v) != 4:
            raise ValueError("options must contain exactly 4 items")
        cleaned = []
        for item in v:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("each option must be a non-empty string")
            cleaned.append(item.strip())
        return cleaned

    @validator("correct_option_index")
    def index_in_range(cls, v):
        if not isinstance(v, int):
            raise ValueError("correct_option_index must be int")
        if v < 0 or v > 3:
            raise ValueError("correct_option_index must be between 0 and 3")
        return v

class ModulePayload(BaseModel):
    module: str
    quizzes: List[Quiz]

class QuizGenerator:
    """
    Generates multiple-choice quizzes for a module using a provided generative model instance.
    The generator expects a model object with a `generate_content(prompt)` method that returns
    an object or dict with a `.text` attribute or key containing the model output.
    """
    def __init__(self, model=None):
        self.model = model

    def _build_prompt(self, module_id, description, num_questions=5):
        return f"""
You are an exam-writer AI. Based only on the conceptual content suggested by the module description below,
create {num_questions} ORIGINAL multiple-choice questions that test understanding of the module's topics.
Do NOT copy or quote sentences verbatim from the description; instead, create new wording based on the ideas.
For each question provide exactly 4 options and indicate which option index (0-3) is correct. Also provide a 1-2 sentence explanation of the correct answer.

Output must be valid JSON ONLY, using this structure:
{{
  "module": "{module_id}",
  "quizzes": [
    {{
      "question": "<question text>",
      "options": ["<opt0>", "<opt1>", "<opt2>", "<opt3>"],
      "correct_option_index": <0|1|2|3>,
      "explanation": "<brief explanation>"
    }}
  ]
}}

Module description (use only as conceptual reference, do not copy):
\"\"\"{description}\"\"\"
"""

    def _extract_json_from_text(self, text: str):
        try:
            return json.loads(text)
        except Exception:
            pass
        m = re.search(r"(\{.*\})", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
        m2 = re.search(r'"module"\s*:\s*"([^"]+)"', text)
        quizzes_m = re.search(r'"quizzes"\s*:\s*(\[[\s\S]*\])', text)
        if quizzes_m:
            mod = m2.group(1) if m2 else None
            try:
                quizzes_json = json.loads(quizzes_m.group(1))
                out = {"module": mod or "", "quizzes": quizzes_json}
                return out
            except Exception:
                pass
        raise ValueError("Could not extract JSON from model response")

    def _coerce_quiz(self, raw) -> Quiz | None:
        if not isinstance(raw, dict):
            return None
        q = {}
        q["question"] = (raw.get("question") or raw.get("prompt") or "").strip()
        opts = raw.get("options")
        if not isinstance(opts, list):
            opts_text = raw.get("options_text") or raw.get("choices") or raw.get("answers") or ""
            if isinstance(opts_text, str) and opts_text.strip():
                parts = [line.strip(" \t-*.0123456789)ABCD:").strip() for line in opts_text.splitlines() if line.strip()]
                opts = parts
        if isinstance(opts, list):
            opts = [str(o).strip() for o in opts if str(o).strip()]
            if len(opts) >= 4:
                opts = opts[:4]
            else:
                return None
        else:
            return None
        q["options"] = opts

        idx = raw.get("correct_option_index")
        if idx is None:
            ans = raw.get("answer") or raw.get("correct") or raw.get("correct_answer")
            if isinstance(ans, str):
                ans_str = ans.strip()
                letter_map = {"A":0,"B":1,"C":2,"D":3}
                if ans_str.upper() in letter_map:
                    idx = letter_map[ans_str.upper()]
                else:
                    try:
                        idx = int(ans_str) - 1
                    except Exception:
                        for i,opt in enumerate(opts):
                            if ans_str.lower() in opt.lower():
                                idx = i
                                break
            elif isinstance(ans, int):
                idx = int(ans)
        try:
            idx = int(idx)
        except Exception:
            return None
        q["correct_option_index"] = idx

        q["explanation"] = (raw.get("explanation") or raw.get("explain") or "").strip()
        try:
            return Quiz.parse_obj(q)
        except ValidationError:
            return None

    def generate_for_module(self, module_id, description, num_questions=5):
        if not self.model:
            raise RuntimeError("Generative model not configured for QuizGenerator.")

        prompt = self._build_prompt(module_id, description, num_questions)
        response = self.model.generate_content(prompt)
        text = getattr(response, "text", None) or (response.get("text") if isinstance(response, dict) else None)
        if not text:
            text = str(response)

        try:
            raw_payload = self._extract_json_from_text(text)
        except Exception as e:
            raise ValueError(f"Failed to extract JSON from model response: {e}\n--- model text ---\n{text[:2000]}") from e

        if not isinstance(raw_payload, dict):
            raise ValueError("Parsed payload is not a JSON object")

        raw_payload_module = raw_payload.get("module") or module_id
        raw_quizzes = raw_payload.get("quizzes", [])

        validated_quizzes = []
        for raw in raw_quizzes[:num_questions]:
            try:
                q = self._coerce_quiz(raw)
            except Exception:
                q = None
            if q:
                validated_quizzes.append(q)
        if not validated_quizzes:
            print(f"⚠️  No valid quizzes parsed for module '{module_id}'. Model output snippet: {text[:500]}")

        final_payload = ModulePayload(module=raw_payload_module or module_id, quizzes=validated_quizzes)
        return final_payload.dict()
