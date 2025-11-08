# agent2/agent2.py
from typing import List, Dict, TypedDict
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from utils.env_loader import get_env

# -------------------------------
# Schema
# -------------------------------
class Description(BaseModel):
    title: str = Field(..., description="Module title")
    description: str = Field(..., description="Detailed module description")

class Agent2State(TypedDict):
    modules: List[str]
    descriptions: List[Dict[str, str]]

# -------------------------------
# LLM Setup
# -------------------------------
OPENAI_API_KEY = get_env("OPENAI_API_KEY")
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.4, api_key=OPENAI_API_KEY)

prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are Agent 2, a course content writer. "
     "You receive a list of module titles and must write one short, informative paragraph "
     "for each module that explains what students will learn. "
     "Return valid JSON with an array of objects like "
     "{{\"descriptions\": [{{\"title\": \"...\", \"description\": \"...\"}}, ...]}}"),
    ("human",
     "Modules: {modules}")
])

structured_llm = llm.with_structured_output(Description)

# -------------------------------
# Core logic
# -------------------------------
def run_agent2(modules: List[str]) -> List[Dict[str, str]]:
    """Generate a description paragraph for each module title."""
    joined_titles = "\n".join(f"- {m}" for m in modules)
    user_prompt = prompt.format(modules=joined_titles)

    # We'll call LLM once per module for finer control
    descriptions = []
    for title in modules:
        text = (
            f"Write a short informative paragraph (60–100 words) "
            f"explaining what a student will learn in the module '{title}'."
        )
        response = llm.invoke(text).content.strip()
        descriptions.append({"title": title, "description": response})
    return descriptions
