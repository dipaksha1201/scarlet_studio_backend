# agent1/agent1.py
from typing import List, Literal, Optional, TypedDict
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from utils.env_loader import get_env

# ---- schema/state ----
class Outline(BaseModel):
    course_title: str = Field(..., description="Short, clear title for the course.")
    topics: List[str] = Field(..., description="List of concise module titles.")

class Agent1State(TypedDict):
    instructor_prompt: str
    level: Literal["beginner", "intermediate", "advanced"]
    modules: int
    course_title: Optional[str]
    outline: Optional[List[str]]

# ---- model ----
OPENAI_API_KEY = get_env("OPENAI_API_KEY")
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, api_key=OPENAI_API_KEY)

prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are Agent 1, a curriculum architect. "
     "Given an instructor's intent, produce an ordered list of concise module titles. "
     "Do not number them, and keep each title under 60 characters. "
     "Return valid JSON exactly in the format: "
     "{{\"course_title\": \"...\", \"topics\": [\"...\", \"...\"]}}"),
    ("human",
     "Instructor prompt: {instructor_prompt}\n"
     "Target level: {level}\n"
     "Target module count: {modules}")
])

structured_llm = llm.with_structured_output(Outline)

# ---- graph node ----
def generate_outline(state: Agent1State) -> Agent1State:
    modules = max(3, min(int(state.get("modules", 6)), 20))
    inputs = {
        "instructor_prompt": state["instructor_prompt"],
        "level": state.get("level", "beginner"),
        "modules": modules,
    }
    result: Outline = structured_llm.invoke(prompt.format(**inputs))
    return {**state, "course_title": result.course_title, "outline": result.topics[:modules]}

# ---- build graph ----
def build_graph():
    g = StateGraph(Agent1State)
    g.add_node("generate_outline", generate_outline)
    g.add_edge(START, "generate_outline")
    g.add_edge("generate_outline", END)
    return g.compile()

# ---- public function used by FastAPI ----
def run_agent1(instructor_prompt: str, level: str = "beginner", modules: int = 6) -> tuple[str, List[str]]:
    app = build_graph()
    init: Agent1State = {
        "instructor_prompt": instructor_prompt,
        "level": level if level in {"beginner", "intermediate", "advanced"} else "beginner",
        "modules": modules,
        "course_title": None,
        "outline": None,
    }
    final = app.invoke(init)
    return final["course_title"], final["outline"]
