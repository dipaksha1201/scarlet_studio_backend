import os
import json
from typing import List
from dotenv import load_dotenv
import google.generativeai as genai
from supabase import create_client, Client

# ============================================================
# ✅ 1. LOAD .env (with debug prints)
# ============================================================

print("🔍 Loading .env…")
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("❌ Supabase URL or SERVICE KEY missing!")

if not GOOGLE_API_KEY:
    raise ValueError("❌ Google API Key missing!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-pro")

# ===============================================================
# ✅ Fetch module + content + learner persona
# ===============================================================


def fetch_module_context(module_id):
    # Fetch module
    mod = supabase.table("modules").select("*").eq("id", module_id).execute()
    if not mod.data:
        raise ValueError("❌ Module not found.")

    module = mod.data[0]
    print("Module found:", module["title"])

    # Fetch course
    course = (
        supabase.table("courses").select("*").eq("id", module["course_id"]).execute()
    )
    print("Course found:", course.data[0]["title"] if course.data else "N/A")

    persona = course.data[0]["learner_persona"] if course.data else "curious learner"
    print("Learner persona:", persona)

    # Fetch lesson content
    contents = (
        supabase.table("contents").select("*").eq("module_id", module_id).execute()
    )

    lesson_blocks = [
        c["generated_text"] for c in contents.data if c.get("generated_text")
    ]

    if not lesson_blocks:
        raise ValueError("❌ No generated_text found for this module in contents.")

    lesson_text = "\n\n".join(lesson_blocks)

    return module, persona, lesson_text


# ===============================================================
# ✅ Create chat session in assessments
# ===============================================================


def create_chat_session(module_id):
    new_chat = {
        "type": "chat_history",
        "content_id": module_id,
        "content": {"messages": []},
    }
    row = supabase.table("assessments").insert(new_chat).execute()
    return row.data[0]["id"]


def append_message(assessment_id, role, text):
    row = (
        supabase.table("assessments")
        .select("*")
        .eq("id", assessment_id)
        .execute()
        .data[0]
    )
    content = row["content"]

    if "messages" not in content:
        content["messages"] = []

    content["messages"].append({"role": role, "text": text})

    supabase.table("assessments").update({"content": content}).eq(
        "id", assessment_id
    ).execute()


# ===============================================================
# ✅ Guardrails
# ===============================================================


def is_in_scope(question: str, lesson_text: str):
    words = [w.lower() for w in question.split()]
    hits = sum(1 for w in words if w in lesson_text.lower())

    return hits > 0  # at least one overlap


# ===============================================================
# ✅ LLM Response
# ===============================================================


def generate_answer(lesson, persona, history, question):
    system_prompt = f"""
You are a personalized Q&A tutor.

Persona: {persona}

RULES:
- Only answer using the lesson content provided.
- If question is off-topic, politely redirect back to the module.
- Keep responses short (2-4 sentences).
- Do NOT add information not found in the lesson.

LESSON CONTENT:
---------------------------
{lesson}
---------------------------
"""

    messages = [{"role": "user", "parts": [system_prompt]}]

    for msg in history:
        messages.append({"role": msg["role"], "parts": [msg["text"]]})

    messages.append({"role": "user", "parts": [question]})

    response = model.generate_content(messages)
    return response.text


# ===============================================================
# ✅ Main Chat Loop (Terminal)
# ===============================================================


def main():
    print("\n✅ Scarlet Q&A Tutor")
    module_id = input("Enter module_id: ").strip()

    module, persona, lesson = fetch_module_context(module_id)

    assessment_id = create_chat_session(module_id)
    print(f"✅ Chat session started: {assessment_id}\n")

    history = []

    while True:
        user_q = input("You: ")

        if user_q.lower() in ["quit", "exit", "bye"]:
            print("👋 Ending chat.")
            break

        # Guardrail check
        if not is_in_scope(user_q, lesson):
            bot = "That question is outside today's module. Let's focus on the lesson."
            print("Tutor:", bot)
            append_message(assessment_id, "user", user_q)
            append_message(assessment_id, "assistant", bot)
            continue

        bot = generate_answer(lesson, persona, history, user_q)
        print("Tutor:", bot)

        # Save messages
        append_message(assessment_id, "user", user_q)
        append_message(assessment_id, "assistant", bot)

        # Update history
        history.append({"role": "user", "text": user_q})
        history.append({"role": "assistant", "text": bot})


if __name__ == "__main__":
    main()
