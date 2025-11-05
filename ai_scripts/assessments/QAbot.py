import os
import time
from typing import TypedDict, List, Tuple

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
import google.generativeai as genai
# We'll use LangChain's message types to store the chat history
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


# Load environment variables
load_result = load_dotenv()
print(f"--- .env file detected? {load_result} ---", flush=True) 

# Configure the Google client
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("Warning: GOOGLE_API_KEY not set.", flush=True)
else:
    genai.configure(api_key=GOOGLE_API_KEY)

# Initialize the Generative Model
# We are NOT using JSON mode here, we want natural text responses.
model = genai.GenerativeModel("gemini-2.5-pro")


class ChatTutorState(TypedDict):
    """
    Defines the memory for our chat agent.
    """
    lesson_content: str
    # The chat_history will be a list of HumanMessage and AIMessage objects
    chat_history: List[BaseMessage]



def build_tutor_prompt(content: str, history: List[BaseMessage]) -> List[dict]:
    """
    Builds the full conversational history for the Gemini API,
    including the system prompt.
    """
    
    # This is the "system prompt" or main instruction for the tutor.
    system_prompt = f"""
    You are an expert AI tutor for a university. Your goal is to assess a student's understanding of the provided lesson.
    
    **Your Persona:**
    - Friendly, encouraging, and Socratic.
    - Never give the answer directly.
    - Ask guiding questions to help the student arrive at the answer themselves.
    - Keep your responses concise (2-3 sentences).

    **Lesson Content (Source of Truth):**
    ---
    {content}
    ---
    
    **Your Task:**
    - **If the chat history is empty:** Ask 1-2 open-ended, introductory questions based on the lesson to start the assessment. 
    - **CRITICAL RULE FOR YOUR FIRST TURN:** Your entire response must be ONLY the 1-2 introductory questions. Do NOT repeat your persona, your instructions, or say "OK, I'm ready". Just ask the questions directly.
    - **If the chat history is NOT empty:**
        1.  Acknowledge the student's last answer (e.g., "That's a great point!", "You're on the right track...", "Not quite, let's think about...").
        2.  Provide brief, guiding feedback.
        3.  Ask a new, relevant follow-up question to probe deeper or move to the next concept.
    """
    
    # Format the LangChain messages into the simple dict format Google's API needs
    # [ {'role': 'user', 'parts': ['...']}, {'role': 'model', 'parts': ['...']} ]
    
    # Start with the system prompt as the first "user" message
    formatted_history = [
        {'role': 'user', 'parts': [system_prompt]}
    ]
    
    # Add the rest of the chat history
    for msg in history:
        role = "user" if isinstance(msg, HumanMessage) else "model"
        formatted_history.append({'role': role, 'parts': [msg.content]})
        
    return formatted_history


def call_tutor_llm(state: ChatTutorState) -> dict:
    """
    This node is the "brain" of the tutor. It calls the LLM.
    """
    print("--- AI Tutor is thinking... ---", flush=True)
    
    # 1. Get state
    content = state['lesson_content']
    history = state['chat_history']
    
    # 2. Build the system instruction and the chat history
    formatted_prompt = build_tutor_prompt(content, history)
    
    # 3. Calling the LLM
    try:
        # Pass the combined prompt/history
        response = model.generate_content(formatted_prompt)
        ai_response_text = response.text
        
        # 4. Add the new AI message to the history
        return {"chat_history": [AIMessage(content=ai_response_text)]}
        
    except Exception as e:
        print(f"Error calling LLM: {e}", flush=True)
        return {"chat_history": [AIMessage(content="Sorry, I ran into an error. Could you try rephrasing that?")]}


def get_student_response(state: ChatTutorState) -> dict:
    """
    This node STOPS the graph and waits for user input.
    """
    # 1. Get the latest AI message from the history
    last_ai_message = state['chat_history'][-1].content
    
    # 2. Print it for the student
    print(f"\nAI Tutor:\n{last_ai_message}\n", flush=True)
    
    # 3. Wait for the student to type a response
    human_input = input("Your response (or type 'quit' to exit): ")
    
    # 4. Add the new human message to the history
    return {"chat_history": [HumanMessage(content=human_input)]}




def check_for_quit(state: ChatTutorState) -> str:
    """
    Checks the last human message to see if we should end the chat.
    """
    last_human_message = state['chat_history'][-1].content
    
    if last_human_message.lower() in ['quit', 'exit', "i'm done", 'stop']:
        print("--- You've ended the chat. Great work! ---", flush=True)
        return "end"
    else:
        return "continue"



print("Building AI Tutor chatbot...", flush=True)

builder = StateGraph(ChatTutorState)

# Add the nodes
builder.add_node("call_tutor_llm", call_tutor_llm)
builder.add_node("get_student_response", get_student_response)

# Set the entry point
builder.set_entry_point("call_tutor_llm")

# Build the graph edges (the loop)
builder.add_edge("call_tutor_llm", "get_student_response")
builder.add_conditional_edges(
    "get_student_response",
    check_for_quit,
    {
        "continue": "call_tutor_llm", # Loop back to the AI
        "end": END
    }
)

# Compile the graph
tutor_chat_graph = builder.compile()

print("Chatbot compiled successfully!", flush=True)



def main():
    """
    Main function to run the chatbot.
    """
    
    script_dir = os.path.dirname(__file__)
    content_file_path = os.path.join(script_dir, "lesson_content.txt")

    try:
        with open(content_file_path, "r") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: 'lesson_content.txt' not found in {script_dir}", flush=True)
        return

    if content:
        # Define the initial input for the graph
        # The history starts empty!
        initial_input = {
            "lesson_content": content,
            "chat_history": [],
        }
        
        print("\n--- Starting AI Tutor Chat ---", flush=True)
        
        # Run the graph. This will now loop until you type 'quit'
        # We use .stream() here instead of .invoke() to run the loop
        for event in tutor_chat_graph.stream(initial_input):
            # .stream() will yield the output of each node as it runs
            # but we don't need to print it here, as the nodes print themselves.
            pass
            
        print("\n--- Chat session finished. ---", flush=True)

if __name__ == "__main__":
    main()

