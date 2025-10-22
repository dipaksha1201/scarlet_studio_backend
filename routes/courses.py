# routes/courses.py
"""
CRUD routes for course management (Instructor Interface).
Uses Supabase client from the shared datalayer.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datalayer import get_supabase_client
from typing import Optional

router = APIRouter()

class CourseCreate(BaseModel):
    instructor_id: str
    title: str
    learning_objectives: Optional[str] = None
    learner_persona: Optional[str] = None
    prerequisites: Optional[str] = None


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    learning_objectives: Optional[str] = None
    learner_persona: Optional[str] = None
    prerequisites: Optional[str] = None


# -------------------------
# API routes
# -------------------------
@router.post("/", tags=["Courses"])
def create_course(payload: CourseCreate):
    """
    Create a new draft course.
    """
    client = get_supabase_client()
    data = payload.dict()

    try:
        result = client.table("courses").insert(data).execute()
        return {"message": "Course created", "data": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create course: {e}")


@router.put("/{course_id}", tags=["Courses"])
def update_course(course_id: str, payload: CourseUpdate):
    """
    Update an existing draft course.
    """
    client = get_supabase_client()
    data = {k: v for k, v in payload.dict().items() if v is not None}

    try:
        result = client.table("courses").update(data).eq("id", course_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Course not found")
        return {"message": "Course updated", "data": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update course: {e}")


@router.get("/instructor/{instructor_id}", tags=["Courses"])
def get_instructor_courses(instructor_id: str):
    """
    Get all courses belonging to an instructor.
    """
    client = get_supabase_client()
    try:
        result = client.table("courses").select("*").eq("instructor_id", instructor_id).execute()
        return {"courses": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch instructor courses: {e}")


@router.post("/{course_id}/publish", tags=["Courses"])
def publish_course(course_id: str):
    """
    Mark a course as 'published'.
    """
    client = get_supabase_client()
    try:
        result = (
            client.table("courses")
            .update({"status": "published"})
            .eq("id", course_id)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Course not found")
        return {"message": "Course published", "data": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish course: {e}")


@router.get("/{course_id}/modules", tags=["Courses"])
def get_modules_for_course(course_id: str):
    """
    Retrieve all modules for a given course (mock data if none).
    """
    client = get_supabase_client()
    try:
        result = client.table("modules").select("*").eq("course_id", course_id).execute()
        if not result.data:
            return {
                "modules": [
                    {
                        "id": "mock-1",
                        "title": "Getting Started",
                        "description": "Introductory module (placeholder).",
                    }
                ]
            }
        return {"modules": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get modules: {e}")
