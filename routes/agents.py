# routes/agents_gemini.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from services.module_gen import GeminiModuleAgent
from services.module_service import ModuleService
from utils.auth import get_optional_user_id


from services.content_gen import GeminiContentAgent
from services.content_service import ContentService
from pydantic import BaseModel


router = APIRouter()

# Lazy initialization - don't instantiate until first use
_agent = None
_module_service = None

_content_agent = None
_content_service = None


def get_content_agent() -> GeminiContentAgent:
    """Get or create the GeminiContentAgent instance."""
    global _content_agent
    if _content_agent is None:
        _content_agent = GeminiContentAgent()
    return _content_agent

def get_content_service() -> ContentService:
    """Get or create the ContentService instance."""
    global _content_service
    if _content_service is None:
        _content_service = ContentService()
    return _content_service


def get_agent() -> GeminiModuleAgent:
    """Get or create the GeminiModuleAgent instance."""
    global _agent
    if _agent is None:
        _agent = GeminiModuleAgent()
    return _agent

def get_module_service() -> ModuleService:
    """Get or create the ModuleService instance."""
    global _module_service
    if _module_service is None:
        _module_service = ModuleService()
    return _module_service

class ModuleRequest(BaseModel):
    course_id: str
    course_name: str
    learning_objectives: str
    learner_persona: str
    prerequisites: str
    instructor_id: Optional[str] = None  # Optional for backwards compatibility


class ModuleEditRequest(BaseModel):
    course_id: str
    edit_instruction: str
    
    
class ContentRequest(BaseModel):
    module_id: str

class ContentEditRequest(BaseModel):
    module_id: str
    edit_instruction: str


@router.post("/modules/gemini-generate", tags=["AI Agents"])
async def generate_modules_with_gemini(
    payload: ModuleRequest,
    user_id: Optional[str] = Depends(get_optional_user_id)
):
    """
    Generate 3–5 structured course modules using Google's Gemini API.
    The course information and generated modules are automatically stored in the database.
    
    Authentication:
    - If you provide an Authorization header with Bearer token, instructor_id will be auto-set
    - Otherwise, you can manually specify instructor_id in the request body
    - Both are optional but recommended
    
    If the course_id already exists, it will update the course details.
    If it doesn't exist, it will create a new course record.
    """
    try:
        # Use authenticated user ID if available, otherwise use provided instructor_id
        instructor_id = user_id or payload.instructor_id
        
        agent = get_agent()
        modules = agent.generate_modules(
            payload.course_id,
            payload.course_name,
            payload.learning_objectives,
            payload.learner_persona,
            payload.prerequisites,
            instructor_id, # type: ignore
        )
        return {
            "course_id": payload.course_id,
            "modules": modules,
            "instructor_id": instructor_id,
            "message": f"Course and modules saved to database. Use course_id '{payload.course_id}' to edit them."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini generation failed: {e}")


@router.post("/modules/gemini-edit", tags=["AI Agents"])
def edit_modules_with_gemini(payload: ModuleEditRequest):
    """
    Edit existing course modules using natural language instructions.
    Simply reference modules by number in your instruction. Examples:
    - "Make module 1 more concise"
    - "Add more practical examples to module 2"
    - "Change module 1's learning goals to be more beginner-friendly"
    - "Add a new module about Neural Networks after module 3"
    - "Remove module 2 and merge its content with module 3"
    
    The system automatically retrieves the stored modules for the given course_id.
    """
    try:
        agent = get_agent()
        edited_modules = agent.edit_modules(
            payload.course_id,
            payload.edit_instruction,
        )
        return {
            "course_id": payload.course_id,
            "modules": edited_modules,
            "message": "Modules updated successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini module editing failed: {e}")


@router.get("/modules/{course_id}", tags=["AI Agents"])
def get_stored_modules(course_id: str):
    """
    Retrieve the currently stored modules for a course from database.
    Useful for checking what modules exist before editing.
    """
    try:
        module_service = get_module_service()
        modules = module_service.get_modules(course_id)
        return {
            "course_id": course_id,
            "modules": modules
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/modules", tags=["AI Agents"])
def list_all_courses():
    """
    List all course IDs that have stored modules in the database.
    """
    module_service = get_module_service()
    course_ids = module_service.get_all_courses_with_modules()
    return {
        "course_ids": course_ids,
        "count": len(course_ids)
    }


# --- Content Generation Endpoints ---


@router.post("/content/gemini-generate", tags=["AI Agents"])
async def generate_content_with_gemini(payload: ContentRequest):
    """
    Generate 3-5 introductory paragraphs for a specific module using Gemini.
    The generated content is automatically stored in the database.
    """
    try:
        agent = get_content_agent()
        paragraphs = agent.generate_content(payload.module_id)
        return {
            "module_id": payload.module_id,
            "content": paragraphs,
            "message": f"Content paragraphs saved to database for module_id '{payload.module_id}'"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini content generation failed: {e}")


@router.post("/content/gemini-edit", tags=["AI Agents"])
def edit_content_with_gemini(payload: ContentEditRequest):
    """
    Edit existing module content (paragraphs) using natural language.
    The system automatically retrieves, edits, and re-saves the content.
    """
    try:
        agent = get_content_agent()
        edited_paragraphs = agent.edit_content(
            payload.module_id,
            payload.edit_instruction,
        )
        return {
            "module_id": payload.module_id,
            "content": edited_paragraphs,
            "message": "Content updated successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini content editing failed: {e}")


@router.get("/content/{module_id}", tags=["AI Agents"])
def get_stored_content(module_id: str):
    """
Retrieve the currently stored content paragraphs for a module.
    """
    try:
        content_service = get_content_service()
        # Get the full records, not just simple format
        content = content_service.get_content_for_module(module_id)
        return {
            "module_id": module_id,
            "content": content
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))