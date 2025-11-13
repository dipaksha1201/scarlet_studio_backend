"""
Gemini-based Content Generation Service
--------------------------------------
Generates structured paragraphs for a course module.

--- MOCK VERSION ---
This version reads from local JSON files instead of Supabase.
"""

import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List
# Note: We no longer import ContentService or ModuleService

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Use the model name you specified
MODEL_NAME = "gemini-2.0-flash"


class GeminiContentAgent:
    """Encapsulates Gemini logic for paragraph generation."""

    def __init__(self):
        self.model = genai.GenerativeModel(MODEL_NAME)
        # No database services are initialized
        print("✅ GeminiContentAgent initialized in MOCK mode (no database).")

    def _load_prompt_template(self) -> str:
        """Load the base prompt for content generation."""
        with open("services/content_prompt.txt", "r", encoding="utf-8") as f:
            return f.read()
    
    def _load_edit_prompt_template(self) -> str:
        """Load the prompt template for content editing."""
        with open("services/content_edit_prompt.txt", "r", encoding="utf-8") as f:
            return f.read()
    
    def _get_context_for_prompt(self, module_id: str) -> dict:
        """
        Helper to fetch module details from the mock_modules.json file.
        """
        print(f"📚 Reading from services/mock_modules.json for module_id: {module_id}")
        try:
            with open("services/mock_modules.json", "r", encoding="utf-8") as f:
                all_modules = json.load(f)
            
            context = all_modules.get(module_id)
            if not context:
                raise ValueError(f"Module ID '{module_id}' not found in mock_modules.json")
            
            return context
        except Exception as e:
            print(f"❌ Error reading mock_modules.json: {e}")
            raise
    
    def _get_mock_content(self, module_id: str) -> List[str]:
        """
        Helper to fetch content from the mock_content.json file.
        """
        print(f"📚 Reading from services/mock_content.json for module_id: {module_id}")
        try:
            with open("services/mock_content.json", "r", encoding="utf-8") as f:
                all_content = json.load(f)
            
            # Use .get() to handle cases where module_id might be missing
            content = all_content.get(module_id)
            
            if content is None:
                 # If no content exists (e.g., new module), return empty list
                 print(f"⚠️  No mock content found for module_id '{module_id}', returning empty list.")
                 return []
            
            return content
        except Exception as e:
            print(f"❌ Error reading mock_content.json: {e}")
            raise

    def _parse_json_response(self, raw_output: str) -> List[str]:
        """
        Safely parses the Gemini response to extract a JSON list of strings.
        (This function is unchanged from your version)
        """
        print(f"📄 Raw Gemini Output for Parsing:\n{raw_output[:500]}...")
        cleaned_output = raw_output
        if "```" in cleaned_output:
            print("🔧 Removing markdown code fences...")
            cleaned_output = re.sub(r'^```(?:json)?\s*\n?', '', cleaned_output, flags=re.MULTILINE)
            cleaned_output = re.sub(r'\n?```\s*$', '', cleaned_output, flags=re.MULTILINE)
            cleaned_output = cleaned_output.strip()
        array_start = cleaned_output.find('[')
        if array_start == -1:
            print(f"❌ No JSON list found in output!")
            raise Exception("No JSON array found in Gemini response")
        end_idx = cleaned_output.rfind(']')
        if end_idx == -1 or end_idx < array_start:
            print(f"❌ No matching closing bracket found!")
            raise Exception(f"Malformed JSON: no matching ']' found")
        json_str = cleaned_output[array_start:end_idx + 1]
        try:
            paragraphs = json.loads(json_str)
            if not isinstance(paragraphs, list) or not all(isinstance(p, str) for p in paragraphs):
                print(f"❌ JSON is not a list of strings: {type(paragraphs)}")
                raise Exception("JSON response was not in the expected format of a simple list of strings.")
            print(f"✅ Successfully parsed JSON with {len(paragraphs)} paragraphs")
            return paragraphs
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {e}")
            raise Exception(f"Failed to parse JSON: {str(e)}")

    def generate_content(self, module_id: str):
        """Generate paragraphs for a module using Gemini."""
        try:
            context = self._get_context_for_prompt(module_id)
            base_prompt = self._load_prompt_template().format(
                course_name=context["course_name"],
                learning_objectives=context["learning_objectives"],
                module_title=context["module_title"],
                module_description=context["module_description"],
            )
        except Exception as e:
            print(f"❌ Error loading prompt template: {e}")
            raise Exception(f"Failed to load prompt template: {e}")

        print("\n🧠 Generating content using Gemini...\n")
        try:
            response = self.model.generate_content(
                base_prompt,
                generation_config=genai.types.GenerationConfig(temperature=0.7),
            )
            raw_output = response.text.strip()
            paragraphs = self._parse_json_response(raw_output)
            
            # --- MODIFIED ---
            # Instead of saving, we print
            print(f"\n✅--- MOCK SAVE (GENERATE) ---")
            print(f"Would save the following content for module_id '{module_id}':")
            print(json.dumps(paragraphs, indent=2))
            print(f"------------------------------\n")
            # --- END MODIFIED ---
            
            return paragraphs
        except Exception as e:
            print(f"❌ Gemini API call or parsing failed: {e}")
            raise Exception(f"Gemini content generation failed: {e}")
    
    def edit_content(self, module_id: str, edit_instruction: str):
        """Edit existing paragraphs based on instructor's prompt."""
        try:
            # --- MODIFIED ---
            # Retrieve from our mock file instead of database
            current_paragraphs = self._get_mock_content(module_id)
            # --- END MODIFIED ---
            
            current_paragraphs_str = json.dumps(current_paragraphs, indent=2)
            edit_prompt = self._load_edit_prompt_template().format(
                current_paragraphs=current_paragraphs_str,
                edit_instruction=edit_instruction
            )
        except Exception as e:
            print(f"❌ Error preparing edit prompt: {e}")
            raise Exception(f"Failed to prepare edit prompt: {e}")
        
        print("\n✏️  Editing content using Gemini...\n")
        try:
            response = self.model.generate_content(
                edit_prompt,
                generation_config=genai.types.GenerationConfig(temperature=0.7),
            )
            raw_output = response.text.strip()
            edited_paragraphs = self._parse_json_response(raw_output)
            
            # --- MODIFIED ---
            # Instead of saving, we print
            print(f"\n✅--- MOCK SAVE (EDIT) ---")
            print(f"Would save the following EDITED content for module_id '{module_id}':")
            print(json.dumps(edited_paragraphs, indent=2))
            print(f"--------------------------\n")
            # --- END MODIFIED ---
            
            return edited_paragraphs
        except Exception as e:
            print(f"❌ Gemini API call or parsing failed: {e}")
            raise Exception(f"Gemini content editing failed: {e}")