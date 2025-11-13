from typing import TypedDict,List
import google.generativeai as genai
import os
from dotenv import load_dotenv
from scarlet_studio_backend.ai_scripts.flashcard.flashcard_schema import Flashcard
import json

load_result = load_dotenv()
print(f"--- .env file detected? {load_result} ---", flush=True) 

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("Warning: GOOGLE_API_KEY not set. Please check your .env file.", flush=True)
else:
    # Configure the Google client
    genai.configure(api_key=GOOGLE_API_KEY)


generation_config = {
  "response_mime_type": "application/json",
}


model = genai.GenerativeModel(
    "gemini-2.5-pro", 
    generation_config=generation_config
)


class FlashCardState(TypedDict):
    lesson_content:str
    num_flashcards_desired:int
    generated_flashcards:List[Flashcard]
    questions_to_avoid:List[str]



async def build_llm_prompt(content:str,avoid_list:List[str])->str:
    """Helper fucntion to give out the precise prompt for the LLM"""

    if not avoid_list:
        avoid_section="You have not generated any flashcard yet"
    else:
        avoid_section="You have already generated the following questions. Do not repeat them or create simple variations:\n"

    json_schema = """
    {
     "question": "The text of the flashcard question",
     "answer": "The correct answer to the question",
     "explanation": "A short explanation that elaborates on the answer or gives context"

    }"""

    return f"""
    You are an expert educational content creator for an e-learning platform. 
    Your task is to generate one **high-quality flashcard** from the provided lesson content.

    **Lesson Content:**
    ---
    {content}
    ---

    **Rules:**
    1. The flashcard MUST be based only on the provided lesson content.
    2. The question should be concise but thought-provoking.
    3. The 'answer' should directly address the question.
    4. The 'explanation' should help a student understand *why* that answer is correct.
    5. {avoid_section}
    6. Do NOT include phrases like "According to the lesson..." — the flashcard should sound natural.
    7. Output must strictly follow the JSON format below.

    **Output Format (JSON):**
    {json_schema}
    """

def generate_flashcard(state:FlashCardState)->dict:
    """
    Node that generates a new Flashcard based on the lesson content
    and avoiding previously generated questions.
    """

    #print(f"--- Generating Flashcard {len(state['generated_mcqs']) + 1} ---", flush=True)

    content = state['lesson_content']
    avoid_list = state['questions_to_avoid']

    prompt = build_llm_prompt(content,avoid_list)

    response = model.generate_content(prompt)

    card_data = json.loads(response.txt)

    flashcard = Flashcard(
        question=card_data['question'],
        answer=card_data['answer'],
        explanation=card_data['explanation']
    )

    state["generated_flashcards"].append(flashcard)
    state["questions_to_avoid"].append(flashcard.question)
    
    return flashcard