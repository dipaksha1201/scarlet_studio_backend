"""
Module Database Service
-----------------------
Handles all database operations for course modules using Supabase.
"""

from typing import List, Dict, Optional
from datalayer import BaseService, get_supabase_client


class ModuleService(BaseService):
    """Service for managing course modules in Supabase."""
    
    def __init__(self):
        super().__init__()
    
    def ensure_course_exists(self, course_id: str, course_data: Dict) -> Dict:
        """
        Ensure a course exists in the database. Creates it if it doesn't exist,
        updates it if it does.
        
        Args:
            course_id: The course ID (this should match the UUID in courses table)
            course_data: Dictionary with course fields (title, learning_objective, etc.)
            
        Returns:
            The course record from database
        """
        try:
            # First, check if course exists
            existing = self.supabase.table("courses")\
                .select("*")\
                .eq("id", course_id)\
                .execute()
            
            if existing.data:
                # Course exists, update it
                update_data = {k: v for k, v in course_data.items() if v is not None}
                if update_data:
                    result = self.supabase.table("courses")\
                        .update(update_data)\
                        .eq("id", course_id)\
                        .execute()
                    print(f"📝 Updated course: {course_id}")
                    return result.data[0] if result.data else existing.data[0]
                return existing.data[0]
            else:
                # Course doesn't exist, create it
                course_data["id"] = course_id
                result = self.supabase.table("courses")\
                    .insert(course_data)\
                    .execute()
                print(f"✨ Created new course: {course_id}")
                return result.data[0]
                
        except Exception as e:
            print(f"⚠️  Warning: Could not ensure course exists: {e}")
            # Don't fail the whole operation if course table has issues
            return {"id": course_id, **course_data}
    
    def save_modules(self, course_id: str, modules: List[Dict]) -> List[Dict]:
        """
        Save or update modules for a course.
        
        This will:
        1. Delete existing modules for the course
        2. Insert new modules with proper position ordering
        
        Args:
            course_id: The course ID these modules belong to
            modules: List of module dictionaries with title, description, learning_goals
            
        Returns:
            List of saved module records from database
        """
        try:
            # First, delete existing modules for this course
            self.supabase.table("modules").delete().eq("course_id", course_id).execute()
            
            # Prepare modules for insertion
            modules_to_insert = []
            for idx, module in enumerate(modules):
                module_data = {
                    "course_id": course_id,
                    "position": idx + 1,
                    "title": module.get("title", ""),
                    "description": module.get("description", ""),
                    "editable": True
                }
                modules_to_insert.append(module_data)
            
            # Insert all modules
            result = self.supabase.table("modules").insert(modules_to_insert).execute()
            
            print(f"💾 Saved {len(result.data)} modules to database for course_id: {course_id}")
            return result.data
            
        except Exception as e:
            print(f"❌ Error saving modules to database: {e}")
            raise Exception(f"Failed to save modules: {e}")
    
    def get_modules(self, course_id: str) -> List[Dict]:
        """
        Retrieve all modules for a course, ordered by position.
        
        Args:
            course_id: The course ID to fetch modules for
            
        Returns:
            List of module dictionaries
            
        Raises:
            ValueError: If no modules found for the course
        """
        try:
            result = self.supabase.table("modules")\
                .select("*")\
                .eq("course_id", course_id)\
                .order("position")\
                .execute()
            
            if not result.data:
                raise ValueError(f"No modules found for course_id: {course_id}. Please generate modules first.")
            
            print(f"📖 Retrieved {len(result.data)} modules for course_id: {course_id}")
            return result.data
            
        except Exception as e:
            if "No modules found" in str(e):
                raise
            print(f"❌ Error retrieving modules: {e}")
            raise Exception(f"Failed to retrieve modules: {e}")
    
    def get_modules_simple_format(self, course_id: str) -> List[Dict]:
        """
        Get modules in the simple format used by Gemini (just title and description).
        
        Args:
            course_id: The course ID
            
        Returns:
            List of simplified module dictionaries
        """
        modules = self.get_modules(course_id)
        
        # Convert to simple format for Gemini
        simple_modules = []
        for module in modules:
            simple_modules.append({
                "title": module.get("title", ""),
                "description": module.get("description", "")
            })
        
        return simple_modules
    
    def course_has_modules(self, course_id: str) -> bool:
        """
        Check if a course has any modules.
        
        Args:
            course_id: The course ID to check
            
        Returns:
            True if modules exist, False otherwise
        """
        try:
            result = self.supabase.table("modules")\
                .select("id", count="exact")\
                .eq("course_id", course_id)\
                .execute()
            
            return len(result.data) > 0
        except Exception:
            return False
    
    def get_all_courses_with_modules(self) -> List[str]:
        """
        Get all unique course IDs that have modules.
        
        Returns:
            List of course IDs
        """
        try:
            result = self.supabase.table("modules")\
                .select("course_id")\
                .execute()
            
            # Extract unique course_ids
            course_ids = list(set(module["course_id"] for module in result.data))
            return course_ids
        except Exception as e:
            print(f"❌ Error fetching courses: {e}")
            return []
    
    def delete_modules(self, course_id: str) -> None:
        """
        Delete all modules for a course.
        
        Args:
            course_id: The course ID
        """
        try:
            self.supabase.table("modules").delete().eq("course_id", course_id).execute()
            print(f"🗑️  Deleted modules for course_id: {course_id}")
        except Exception as e:
            print(f"❌ Error deleting modules: {e}")
            raise Exception(f"Failed to delete modules: {e}")

