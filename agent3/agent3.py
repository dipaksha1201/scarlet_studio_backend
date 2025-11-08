# agent3/agent3.py
from typing import List, Dict, TypedDict
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from utils.env_loader import get_env

# ------------------------------
# Schemas
# ------------------------------
class AssessmentItem(BaseModel):
    question: str = Field(..., description="Question text")
    answer: str = Field(..., description="Answer or correct option")

class ModuleAssessment(BaseModel):
    title: str
    type: str  # mcq | qa | flashcards
    items: List[Dict[str, str]]

class Agent3State(TypedDict):
    assessments: List[ModuleAssessment]

# ------------------------------
# LLM Setup
# ------------------------------
OPENAI_API_KEY = get_env("OPENAI_API_KEY")
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.6, api_key=OPENAI_API_KEY)

# ------------------------------
# Core Logic
# ------------------------------
def run_agent3(assessments: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Generate assessments per module based on instructor's selected type.
    Each module can have MCQs, Q&A, or Flashcards.
    """
    results = []

    for module in assessments:
        title = module["title"]
        desc = module["description"]
        atype = module["type"].lower()

        if atype == "mcq":
            instruction = (
                "Create 3 multiple-choice questions (MCQs) with 4 options each "
                f"and clearly mark the correct answer. Focus on key ideas from '{title}'."
            )
        elif atype == "qa":
            instruction = (
                "Create 3 short Q&A pairs where each question encourages understanding "
                f"of '{title}' and its key concepts."
            )
        elif atype == "flashcards":
            instruction = (
                "Create 3 flashcards for '{title}'. Each should have a front (question/term) "
                "and back (definition or explanation)."
            )
        else:
            instruction = (
                "Create 3 general questions and answers based on the content."
            )

        prompt = f"""
        Module Title: {title}
        Module Description: {desc}
        Task: {instruction}
        Format the output in a clean, readable list.
        """

        response = llm.invoke(prompt).content.strip()
        results.append({
            "title": title,
            "type": atype,
            "items": [{"content": response}]
        })

    return results
