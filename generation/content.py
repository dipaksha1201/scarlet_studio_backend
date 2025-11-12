# generation/content.py
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai
from .module import QuizGenerator, ModulePayload

def generate_quizzes_from_static(output_path=None, num_per_module=5):
    """
    Read data/static_module.json, generate `num_per_module` quizzes per module using QuizGenerator,
    validate with ModulePayload, and write combined JSON to data/quiz_output.json (or provided output_path).
    """
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment (.env).")
        return None

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("models/gemini-2.5-flash")

    input_path = os.path.join("data", "static_module.json")
    if not os.path.exists(input_path):
        print("❌ static_module.json not found in data/.")
        return None

    with open(input_path, "r") as f:
        data = json.load(f)

    modules = data.get("modules", [])
    result = {}
    generator = QuizGenerator(model=model)

    for mod in modules:
        module_id = mod.get("module") or mod.get("id") or "unknown_module"
        description = mod.get("description", "")
        print(f"Generating quizzes for module: {module_id} ...")
        try:
            payload = generator.generate_for_module(module_id, description, num_questions=num_per_module)
            try:
                validated = ModulePayload.parse_obj(payload)
            except Exception as ve:
                print(f"⚠️  Validation failed for module {module_id}: {ve}")
                validated = ModulePayload(module=module_id, quizzes=[])
            payload_dict = validated.dict()
        except Exception as e:
            print(f"⚠️  Failed to generate for {module_id}: {e}")
            payload_dict = {"module": module_id, "quizzes": []}
        result[module_id] = {
            "description": description,
            "quizzes": payload_dict.get("quizzes", [])
        }

    output_path = output_path or os.path.join("data", "quiz_output.json")
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"✅ Quiz output saved to {output_path}")
    return output_path
