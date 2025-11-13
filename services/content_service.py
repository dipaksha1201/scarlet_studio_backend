"""
Content Database Service
-----------------------
Handles all database operations for module content.
Matches the 'contents' table schema.
"""

from typing import List, Dict
from datalayer import BaseService
import json

class ContentService(BaseService):
    """Service for managing module content (paragraphs) in Supabase."""
    
    def __init__(self):
        super().__init__()
    
    def save_content_paragraphs(self, module_id: str, paragraphs: List[str]) -> Dict:
        """
        Save or update paragraphs for a module.
        
        This will:
        1. Convert the list of paragraphs into a single text block.
        2. "Upsert" the content, creating a new row if one doesn't exist
           or updating the existing one for the module_id.
        
        Args:
            module_id: The module ID these paragraphs belong to
            paragraphs: List of paragraph strings
            
        Returns:
            The saved content record from database
        """
        try:
            # Convert the list of paragraphs into a single text block
            # We'll join them with a double newline for separation.
            content_to_save = "\n\n".join(paragraphs)
            
            data_to_upsert = {
                "module_id": module_id,
                "generated_text": content_to_save,
                "is_edited": True # We assume saving is an edit or new content
                # We can also add last_prompt if the agent provides it
            }
            
            # Upsert: Insert if it doesn't exist, update if it does.
            result = self.supabase.table("contents")\
                .upsert(data_to_upsert, on="module_id")\
                .execute()
            
            print(f"💾 Saved content to database for module_id: {module_id}")
            return result.data[0]
            
        except Exception as e:
            print(f"❌ Error saving content to database: {e}")
            raise Exception(f"Failed to save content: {e}")
    
    def get_content_for_module(self, module_id: str) -> Dict:
        """
        Retrieve the content for a module.
        
        Args:
            module_id: The module ID to fetch content for
            
        Returns:
            The content dictionary
            
        Raises:
            ValueError: If no content found for the module
        """
        try:
            result = self.supabase.table("contents")\
                .select("*")\
                .eq("module_id", module_id)\
                .single()\
                .execute()
            
            if not result.data:
                raise ValueError(f"No content found for module_id: {module_id}. Please generate content first.")
            
            print(f"📖 Retrieved content for module_id: {module_id}")
            return result.data
            
        except Exception as e:
            if "No content found" in str(e) or "single" in str(e):
                raise ValueError(f"No content found for module_id: {module_id}")
            
            print(f"❌ Error retrieving content: {e}")
            raise Exception(f"Failed to retrieve content: {e}")
    
    def get_content_simple_format(self, module_id: str) -> List[str]:
        """
        Get paragraphs in the simple list format used by Gemini.
        
        Args:
            module_id: The module ID
            
        Returns:
            List of paragraph strings
        """
        try:
            content_data = self.get_content_for_module(module_id)
            
            # Get the single text block from the DB
            full_text = content_data.get("generated_text", "")
            
            if not full_text:
                return []
            
            # Split the text block back into a list of paragraphs
            simple_content = full_text.split("\n\n")
            return simple_content
        
        except ValueError:
            # If no content exists yet, just return an empty list
            return []