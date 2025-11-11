import os
import json
from typing import List
from dotenv import load_dotenv
import google.generativeai as genai


# --------------------------------------------------
# Load environment
# --------------------------------------------------
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("Missing GOOGLE_API_KEY in .env")

# Configure the Google client
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-pro")


# --------------------------------------------------
# Load Module Content From content.json
# --------------------------------------------------
def load_module_content(module_id: str) -> str:
    json_path = os.path.join(os.path.dirname(__file__), "content.json")
    if not os.path.exists(json_path):
        raise FileNotFoundError("content.json missing.")

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except UnicodeDecodeError as e:
        raise UnicodeDecodeError(
            e.encoding or "utf-8",
            e.object,
            e.start,
            e.end,
            f"Failed to decode content.json. Ensure the file is saved as UTF-8. Original: {e}",
        )

    if not isinstance(data, list):
        raise ValueError("content.json must be a JSON array of objects.")

    # Filter by module_id; accept either 'generated_text' or 'text' as payload key
    chunks: List[str] = []
    for item in data:
        if item.get("module_id") == module_id:
            payload = item.get("generated_text") or item.get("text")
            if isinstance(payload, str) and payload.strip():
                chunks.append(payload.strip())

    if not chunks:
        raise ValueError(f"No content found for module_id: {module_id}")

    return "\n\n".join(chunks)


# --------------------------------------------------
# Build Prompt With Guardrails
# --------------------------------------------------
def build_prompt(lesson_content: str, history: List[dict]) -> List[dict]:
    system_prompt = f"""
You are a university Q&A tutor. Your knowledge is STRICTLY LIMITED to the following module:

==========================
{lesson_content}
==========================

RULES:
- Answer ONLY using the above content.
- If the user asks something outside the content, respond: "I can only answer based on the current module content."
- Be short, and clear.
- Set the tone: professor in a university course.
"""

    # Start the conversation by injecting the guardrails
    messages = [{"role": "user", "parts": [system_prompt]}]

    # Then append the running dialogue
    for turn in history:
        # Ensure roles are only 'user' or 'model'
        role = "user" if turn["role"] == "user" else "model"
        messages.append({"role": role, "parts": [turn["content"]]})

    return messages


# --------------------------------------------------
# Save chat history locally
# --------------------------------------------------
def save_history(module_id: str, history: List[dict]):
    history_file = "chat_history.json"

    # Load old history if exists
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                full_history = json.load(f)
        except Exception:
            full_history = {}
    else:
        full_history = {}

    # Append to module-specific history
    if module_id not in full_history:
        full_history[module_id] = []

    full_history[module_id].extend(history)

    # Save back
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(full_history, f, indent=2, ensure_ascii=False)


# --------------------------------------------------
# Main Chat Loop
# --------------------------------------------------
def main():
    print("  Scarlet Q&A Tutor\n")

    module_id = input("Enter module_id: ").strip()
    print("Loading module content...")

    try:
        lesson_content = load_module_content(module_id)
    except Exception as e:
        print(f"\nError loading module content: {e}")
        return

    print("\n  Module loaded. Ask questions about this module. Type 'quit' to exit.\n")

    chat_history: List[dict] = []

    try:
        while True:
            user_msg = input("Your question (or 'quit'): ").strip()
            if user_msg.lower() in {"quit", "exit", "stop"}:
                break
            if not user_msg:
                continue

            # Save user message
            chat_history.append({"role": "user", "content": user_msg})

            # Build prompt (guardrails + full history)
            messages = build_prompt(lesson_content, chat_history)

            # LLM call
            print("\nthinking...\n")
            try:
                response = model.generate_content(messages)
                ai_text = (response.text or "(No response)").strip()
            except Exception as e:
                ai_text = f"Model error: {e}"

            # Show response
            print(ai_text)

            # Save AI message
            chat_history.append({"role": "model", "content": ai_text})
    finally:
        print("\nEnding chat. Saving history...")
        try:
            save_history(module_id, chat_history)
            print("Chat saved to chat_history.json")
        except Exception as e:
            print(f"Failed to save chat history: {e}")


if __name__ == "__main__":
    main()
