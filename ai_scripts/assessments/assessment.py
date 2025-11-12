
import os
import json
import time 
from typing import TypedDict, List

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
# Import the Google generativeai library
import google.generativeai as genai


from assessment_schema import MCQ 



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



class McqGenerationState(TypedDict):
    """
    Defines the "memory" or state of our graph.
    This state is passed between nodes.
    """
    lesson_content: str
    num_questions_desired: int
    generated_mcqs: List[MCQ]
    questions_to_avoid: List[str]


def build_llm_prompt(content: str, avoid_list: List[str]) -> str:
    """Helper function to build the precise prompt for the LLM."""
    
    # Format the list of questions to avoid
    if not avoid_list:
        avoid_section = "You have not generated any questions yet."
    else:
        avoid_section = "You have already generated the following questions. Do not repeat them or create simple variations:\n"
        for i, q_text in enumerate(avoid_list):
            avoid_section += f"- {q_text}\n"

    # Define the desired JSON structure for the LLM
    # even though we've set the response_mime_type.
    json_schema = """
    {
      "question_text": "The text of the multiple-choice question",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "The string of the correct option"
    }
    """

    return f"""
    You are an expert quiz creator for an e-learning platform for a university. Your task is to generate one high-quality, multiple-choice question based on the provided lesson content.

    **Lesson Content:**
    ---
    {content}
    ---

    **Rules:**
    1.  The question MUST be based *only* on the lesson content provided.
    2.  You MUST generate exactly 4 options.
    3.  The 'correct_answer' MUST exactly match one of the strings in the 'options' list.
    4.  {avoid_section}
    5.  **NEW RULE:** Do NOT use repetitive lead-in phrases like "According to the lesson content...", "Based on the provided text...", or "According to the provided text...". The question should be direct and natural.

    **Output Format:**
    You MUST respond with *only* a single, valid JSON object matching this schema. Do not include any other text, markdown, or explanations.
    
    **JSON Schema:**
    {json_schema}
    """

def generate_one_mcq(state: McqGenerationState) -> dict:
    """
    Node that generates a single, new MCQ based on the lesson content
    and avoiding previously generated questions.
    """
    print(f"--- Generating Question {len(state['generated_mcqs']) + 1} ---", flush=True)
    
    content = state['lesson_content']
    avoid_list = state['questions_to_avoid']
    
    
    prompt = build_llm_prompt(content, avoid_list)
    
    
    response = None
    response_json_str = "" 
    
    try:
        # 2. Call the Google Gemini API
        response = model.generate_content(prompt)
        
        # 3. Parse the LLM's JSON output
        # The JSON string is in response.text
        response_json_str = response.text
        response_data = json.loads(response_json_str)
        
        # 4. Use the Pydantic model to parse and validate the data
        new_mcq = MCQ(
            question_text=response_data['question_text'],
            options=response_data['options'],
            correct_answer=response_data['correct_answer']
        )
        
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON from LLM. Response: {response_json_str}\nError: {e}", flush=True)
        return {} # Return no changes if JSON is bad
    except Exception as e:
        print(f"Error validating LLM output or calling API: {e}", flush=True)
        # Handle potential API errors (e.g., blockages, key issues)
        # Now 'response' will be None if the API call failed
        if response and hasattr(response, 'prompt_feedback'):
             print(f"API Error: {response.prompt_feedback}", flush=True)
        return {} 

    print(f"Successfully generated: {new_mcq.question_text}", flush=True)
    
    
    return {
        "generated_mcqs": state["generated_mcqs"] + [new_mcq],
        "questions_to_avoid": state["questions_to_avoid"] + [new_mcq.question_text]
    }



def should_continue_generation(state: McqGenerationState) -> str:
    """
    Determines whether to continue generating more questions or to end.
    """
    num_generated = len(state['generated_mcqs'])
    num_desired = state['num_questions_desired']
    
    print(f"--- Checking: {num_generated} generated, {num_desired} desired ---", flush=True)
    
    if num_generated < num_desired:
        print("Decision: Continue", flush=True)
        print("--- Waiting 65s because of free tier rate limit... ---", flush=True)
        time.sleep(65)
        return "continue"
    
    
    else:
        print("Decision: End", flush=True)
        return "end"


def create_mcq_graph() -> StateGraph:
    """
    Builds and compiles the LangGraph state machine.
    """
    print("Building MCQ generation graph...", flush=True)
    
    builder = StateGraph(McqGenerationState)
    
    # Add the single node for generating questions
    builder.add_node("generate_mcq", generate_one_mcq)
    
    # Set the entry point for the graph
    builder.set_entry_point("generate_mcq")
    
    # Add the conditional edge that creates the loop
    builder.add_conditional_edges(
        "generate_mcq",
        should_continue_generation,
        {
            "continue": "generate_mcq", 
            "end": END
        }
    )
    
    # Compile the graph
    graph = builder.compile()
    print("Graph is compiled successfully!", flush=True)
    return graph

# Create the graph instance to be imported by other files
mcq_graph = create_mcq_graph()



def main():
    """
    Main function to test the 'mcq_graph' when this script is run directly.
    """
    
    # Find the directory this script is in
    script_dir = os.path.dirname(__file__)
    # Create a path to 'lesson_content.txt' in that *same* directory
    content_file_path = os.path.join(script_dir, "lesson_content.txt")

    try:
        with open(content_file_path, "r") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: 'lesson_content.txt' not found in {script_dir}", flush=True)
        print("Please create it in the 'scarlet_studio_backend/ai_scripts/assesments' folder.", flush=True)
        content = "" # Set to empty to avoid crashing

    if content:
        # Define the initial input for the graph
        initial_input = {
            "lesson_content": content,
            "num_questions_desired": 5, # Let's generate 5 questions
            "generated_mcqs": [],
            "questions_to_avoid": []
        }
        
        print("\n--- Invoking Graph ---", flush=True)
        
        # Run the graph
        final_state = mcq_graph.invoke(initial_input)
        
        print("\n--- Graph execution finished ---", flush=True)
        
        # Print the final generated MCQs
        print("\nFinal Generated MCQs:", flush=True)
        for i, mcq in enumerate(final_state['generated_mcqs']):
            print(f"\nQuestion {i+1}:", flush=True)
            print(f"  Text: {mcq.question_text}", flush=True)
            print(f"  Options: {mcq.options}", flush=True)
            print(f"  Answer: {mcq.correct_answer}", flush=True)

# This block ensures that the 'main()' function is only called

if __name__ == "__main__":
    main()

