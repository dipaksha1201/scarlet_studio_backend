"""
Gemini-based Module Generation Service
--------------------------------------
Generates 3–5 structured course modules based on:
Course name, Learning Objectives, Target Persona, and Prerequisites.
"""

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List
from services.module_service import ModuleService

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

MODEL_NAME = "gemini-2.0-flash"


class GeminiModuleAgent:
    """Encapsulates Gemini logic for module generation."""

    def __init__(self):
        self.model = genai.GenerativeModel(MODEL_NAME)
        self.module_service = ModuleService()

    def _load_prompt_template(self) -> str:
        """Load the base prompt for module generation."""
        with open("services/module_prompt.txt", "r", encoding="utf-8") as f:
            return f.read()
    
    def _load_edit_prompt_template(self) -> str:
        """Load the prompt template for module editing."""
        with open("services/module_edit_prompt.txt", "r", encoding="utf-8") as f:
            return f.read()

    def generate_modules(self, course_id: str, course_name: str, learning_objectives: str, learner_persona: str, prerequisites: str, instructor_id: str = None):
        """Generate course modules using Gemini and save course to database."""
        
        # First, ensure the course exists in the database
        course_data = {
            "title": course_name,
            "learning_objective": learning_objectives,
            "learner_persona": learner_persona,
            "prerequisites": prerequisites,
        }
        if instructor_id:
            course_data["instructor_id"] = instructor_id
        
        self.module_service.ensure_course_exists(course_id, course_data)
        
        try:
            base_prompt = self._load_prompt_template().format(
                course_name=course_name,
                learning_objectives=learning_objectives,
                learner_persona=learner_persona,
                prerequisites=prerequisites,
            )
        except Exception as e:
            print(f"❌ Error loading prompt template: {e}")
            raise Exception(f"Failed to load prompt template: {e}")

        print("\n🧠 Generating modules using Gemini...\n")

        try:
            response = self.model.generate_content(
                base_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.9,
                    max_output_tokens=800,
                ),
            )
        except Exception as e:
            print(f"❌ Gemini API call failed: {e}")
            raise Exception(f"Gemini API call failed: {e}")

        # Check if response was blocked or empty
        if not response.candidates:
            print("❌ No response candidates from Gemini")
            raise Exception("Gemini returned no response candidates. Check your API key or content safety settings.")
        
        try:
            raw_output = response.text.strip()
            print(f"\n{'='*60}")
            print(f"📄 FULL RAW GEMINI OUTPUT:")
            print(f"{'='*60}")
            print(raw_output)
            print(f"{'='*60}\n")
        except Exception as e:
            print(f"❌ Error accessing response.text: {e}")
            print(f"Response object: {response}")
            print(f"Response candidates: {response.candidates}")
            raise Exception(f"Failed to extract text from Gemini response: {e}")

        # Parse JSON safely
        import re
        
        # Step 1: Remove markdown code fences if present
        cleaned_output = raw_output
        if "```" in cleaned_output:
            print("🔧 Removing markdown code fences...")
            # Remove opening code fence (```json or ```)
            cleaned_output = re.sub(r'^```(?:json)?\s*\n?', '', cleaned_output, flags=re.MULTILINE)
            # Remove closing code fence
            cleaned_output = re.sub(r'\n?```\s*$', '', cleaned_output, flags=re.MULTILINE)
            cleaned_output = cleaned_output.strip()
            print(f"After fence removal: {cleaned_output[:100]}...")
        
        # Step 2: Find and extract the JSON array/object
        print("🔍 Searching for JSON structure...")
        
        # Look for the first '[' or '{'
        array_start = cleaned_output.find('[')
        object_start = cleaned_output.find('{')
        
        if array_start == -1 and object_start == -1:
            print(f"❌ No JSON structure found in output!")
            print(f"Cleaned output: {cleaned_output}")
            raise Exception("No JSON array or object found in Gemini response")
        
        # Use whichever comes first
        if array_start != -1 and (object_start == -1 or array_start < object_start):
            start_idx = array_start
            end_char = ']'
            print(f"Found JSON array starting at position {start_idx}")
        else:
            start_idx = object_start
            end_char = '}'
            print(f"Found JSON object starting at position {start_idx}")
        
        # Find the last occurrence of the closing character
        end_idx = cleaned_output.rfind(end_char)
        
        if end_idx == -1 or end_idx < start_idx:
            print(f"❌ No matching closing bracket found!")
            raise Exception(f"Malformed JSON: no matching '{end_char}' found")
        
        json_str = cleaned_output[start_idx:end_idx + 1]
        print(f"📦 Extracted JSON (length: {len(json_str)} chars)")
        print(f"First 100 chars: {json_str[:100]}")
        print(f"Last 100 chars: {json_str[-100:]}")
        
        # Step 3: Parse the JSON
        try:
            modules = json.loads(json_str)
            print(f"✅ Successfully parsed JSON with {len(modules) if isinstance(modules, list) else 'N/A'} modules")
            
            # Step 4: Clean modules - only keep title and description
            cleaned_modules = []
            for module in modules:
                cleaned_module = {
                    "title": module.get("title", ""),
                    "description": module.get("description", "")
                }
                # Warn if Gemini added extra fields
                extra_fields = [k for k in module.keys() if k not in ["title", "description"]]
                if extra_fields:
                    print(f"⚠️  Removed extra fields from module: {extra_fields}")
                cleaned_modules.append(cleaned_module)
            
            # Store the cleaned modules in database
            self.module_service.save_modules(course_id, cleaned_modules)
            
            return cleaned_modules
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {e}")
            print(f"Error at position {e.pos}")
            print(f"Context around error: ...{json_str[max(0, e.pos-50):min(len(json_str), e.pos+50)]}...")
            raise Exception(f"Failed to parse JSON: {str(e)}")
    
    def edit_modules(self, course_id: str, edit_instruction: str):
        """Edit existing modules based on instructor's prompt."""
        try:
            # Retrieve the stored modules for this course from database
            current_modules = self.module_service.get_modules_simple_format(course_id)
            
            # Convert modules to formatted JSON string for the prompt
            current_modules_str = json.dumps(current_modules, indent=2)
            
            edit_prompt = self._load_edit_prompt_template().format(
                current_modules=current_modules_str,
                edit_instruction=edit_instruction
            )
        except Exception as e:
            print(f"❌ Error preparing edit prompt: {e}")
            raise Exception(f"Failed to prepare edit prompt: {e}")
        
        print("\n✏️  Editing modules using Gemini...\n")
        print(f"📝 Edit instruction: {edit_instruction}")
        
        try:
            response = self.model.generate_content(
                edit_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.9,
                    max_output_tokens=1500,  # More tokens for editing potentially longer content
                ),
            )
        except Exception as e:
            print(f"❌ Gemini API call failed: {e}")
            raise Exception(f"Gemini API call failed: {e}")
        
        # Check if response was blocked or empty
        if not response.candidates:
            print("❌ No response candidates from Gemini")
            raise Exception("Gemini returned no response candidates. Check your API key or content safety settings.")
        
        try:
            raw_output = response.text.strip()
            print(f"\n{'='*60}")
            print(f"📄 GEMINI EDIT OUTPUT:")
            print(f"{'='*60}")
            print(raw_output)
            print(f"{'='*60}\n")
        except Exception as e:
            print(f"❌ Error accessing response.text: {e}")
            raise Exception(f"Failed to extract text from Gemini response: {e}")
        
        # Parse JSON safely (reuse the same logic as generate_modules)
        import re
        
        # Step 1: Remove markdown code fences if present
        cleaned_output = raw_output
        if "```" in cleaned_output:
            print("🔧 Removing markdown code fences...")
            cleaned_output = re.sub(r'^```(?:json)?\s*\n?', '', cleaned_output, flags=re.MULTILINE)
            cleaned_output = re.sub(r'\n?```\s*$', '', cleaned_output, flags=re.MULTILINE)
            cleaned_output = cleaned_output.strip()
        
        # Step 2: Find and extract the JSON array/object
        array_start = cleaned_output.find('[')
        object_start = cleaned_output.find('{')
        
        if array_start == -1 and object_start == -1:
            print(f"❌ No JSON structure found in output!")
            raise Exception("No JSON array or object found in Gemini response")
        
        # Use whichever comes first
        if array_start != -1 and (object_start == -1 or array_start < object_start):
            start_idx = array_start
            end_char = ']'
        else:
            start_idx = object_start
            end_char = '}'
        
        end_idx = cleaned_output.rfind(end_char)
        
        if end_idx == -1 or end_idx < start_idx:
            raise Exception(f"Malformed JSON: no matching '{end_char}' found")
        
        json_str = cleaned_output[start_idx:end_idx + 1]
        
        # Step 3: Parse the JSON
        try:
            edited_modules = json.loads(json_str)
            print(f"✅ Successfully parsed edited modules: {len(edited_modules) if isinstance(edited_modules, list) else 'N/A'} modules")
            
            # Step 4: Clean modules - only keep title and description
            cleaned_modules = []
            for module in edited_modules:
                cleaned_module = {
                    "title": module.get("title", ""),
                    "description": module.get("description", "")
                }
                # Warn if Gemini added extra fields
                extra_fields = [k for k in module.keys() if k not in ["title", "description"]]
                if extra_fields:
                    print(f"⚠️  Removed extra fields from edited module: {extra_fields}")
                cleaned_modules.append(cleaned_module)
            
            # Store the cleaned updated modules in database
            self.module_service.save_modules(course_id, cleaned_modules)
            
            return cleaned_modules
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {e}")
            raise Exception(f"Failed to parse JSON: {str(e)}")
