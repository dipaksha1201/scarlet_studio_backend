from typing import TypedDict,List
import google.generativeai as genai
import os
from dotenv import load_dotenv
from scarlet_studio_backend.ai_scripts.flashcard.flashcard_schema import Flashcard
import json
from langgraph.graph import StateGraph, END

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

async def generate_flashcard(state:FlashCardState)->dict:
    """
    Node that generates a new Flashcard based on the lesson content
    and avoiding previously generated questions.
    """

    #print(f"--- Generating Flashcard {len(state['generated_mcqs']) + 1} ---", flush=True)

    content = state['lesson_content']
    avoid_list = state['questions_to_avoid']

    prompt = await build_llm_prompt(content,avoid_list)

    response = model.generate_content(prompt)

    card_data = json.loads(response.text)

    flashcard = Flashcard(
        question=card_data['question'],
        answer=card_data['answer'],
        explanation=card_data['explanation']
    )

    state["generated_flashcards"].append(flashcard)
    state["questions_to_avoid"].append(flashcard.question)
    
    return flashcard

async def should_continue_generation(state:FlashCardState)->str:
    """
    Determines whether to continue generating more flashcards or to end.
    """
    num_generated = len(state['generated_flashcards'])
    num_desired = state['num_flashcards_desired']
    
    print(f"--- Checking: {num_generated} generated, {num_desired} desired ---", flush=True)
    
    if num_generated < num_desired:
        print("Decision: Continue", flush=True)
        return "continue"
    else:
        print("Decision: End", flush = True)
        return "end"

async def create_flashcard_graph()->StateGraph:
    """
    Builds and compiles the LangGraph state machine.
    """
    print("Building Flashcard generation graph...", flush=True)
    
    builder = StateGraph(FlashCardState)
    
    # Add the single node for generating flashcards
    builder.add_node("generate_flashcard", generate_flashcard)
    
    # Set the entry point for the graph
    builder.set_entry_point("generate_flashcard")

    # Add the conditional edge that creates the loop
    builder.add_conditional_edges(
        "generate_flashcard",
        should_continue_generation,
        {
            "continue": "generate_flashcard",
            "end": END
        }
    )
    
    
    # Compile the graph
    flashcard_graph = builder.compile()
    print("Flashcard generation graph compiled successfully!", flush=True)
    return flashcard_graph

def main():
    """
    Main function to test the 'flashcard_graph' when this script is run directly.
    """
    print("Starting Flashcard generation...", flush=True)
    
    # Find the directory this script is in
    script_dir = os.path.dirname(__file__)
    # Create a path to 'lesson_content.txt' in that *same* directory
    content_file_path = os.path.join(script_dir, "lesson_content.txt")

    try:
        with open(content_file_path, "r") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: 'lesson_content.txt' not found in {script_dir}", flush=True)
        print("Please create it in the 'scarlet_studio_backend/ai_scripts/flashcard' folder.", flush=True)
        content = "" # Set to empty to avoid crashing

    if content:
        flashcard_graph = create_flashcard_graph()

        initial_input = {
            "lesson_content": content,
            "num_flashcards_desired": 5,
            "generated_flashcards": [],
            "questions_to_avoid": []
        }
        
        print("\n--- Invoking Graph ---", flush=True)
        
        # Run the graph
        final_state = flashcard_graph.invoke(initial_input)
        
        print("\n--- Graph execution finished ---", flush=True)
        
        # Print the final generated flashcards
        print("\nFinal Generated Flashcards:", flush=True)
        for i, flashcard in enumerate(final_state['generated_flashcards']):
            print(f"\nFlashcard {i+1}:", flush=True)
            print(f"  Question: {flashcard.question}", flush=True)
            print(f"  Answer: {flashcard.answer}", flush=True)
            print(f"  Explanation: {flashcard.explanation}", flush=True)

if __name__ == "__main__":
    main()