AI Tutor Backend (FastAPI + OpenAI)

Overview
--------
This project implements a modular AI Tutor Backend using FastAPI, built for multi-agent orchestration.
It currently supports:
 - Agent 1: Course Outline Generator
 - Agent 2: Module Content Generator
 - Agent 3: Assessment Generator (MCQs / Flashcards / Q&A)
 - Pipeline Router: Runs all three agents sequentially

Designed for scalability — you can easily plug in additional agents later.

Project Structure
-----------------
Agent_Orc/
│
├── main.py                     # FastAPI entrypoint
├── requirements.txt             # Python dependencies
│
├── .env                         # API keys (ignored by git)
│
├── agent1/
│   └── agent1.py                # Course Outline Generator
│
├── agent2/
│   └── agent2.py                # Module Description Generator
│
├── agent3/
│   └── agent3.py                # Assessment Generator (MCQ / Flashcards / Q&A)
│
├── routers/
│   ├── __init__.py
│   ├── agent1_router.py
│   ├── agent2_router.py
│   ├── agent3_router.py
│   └── pipeline_router.py       # Orchestrates all agents together
│
├── utils/
│   └── env_loader.py            # Loads environment variables safely
│
└── models/
    └── schemas.py               # Pydantic models for input/output validation

Setup Instructions
------------------
1. Clone the repository:
   git clone https://github.com/<your-username>/AI-Tutor-Agent-Orchestrator.git
   cd AI-Tutor-Agent-Orchestrator

2. Create a virtual environment:
   python -m venv venv
   source venv/Scripts/activate  (Windows)
   OR
   source venv/bin/activate      (Mac/Linux)

3. Install dependencies:
   pip install -r requirements.txt

4. Create a .env file in the root directory:
   OPENAI_API_KEY=your_openai_api_key_here

5. Run the backend server:
   uvicorn main:app --reload

Server will start at http://127.0.0.1:8000

API Endpoints
-------------
GET /
Returns:
{"message": "AI Tutor Backend is running 🚀"}

POST /pipeline/run
Runs the complete 3-agent pipeline in sequence.

Request Body Example:
{
  "instructor_prompt": "Introduction to AI",
  "level": "beginner",
  "modules": 4,
  "assessment_preferences": ["mcq", "flashcards", "qa", "mcq"]
}

Response Example:
{
  "course_title": "Introduction to Artificial Intelligence",
  "modules": [
    "What is Artificial Intelligence?",
    "History of AI",
    "Applications of AI",
    "Ethics and Future of AI"
  ],
  "descriptions": [
    "This module introduces core AI concepts...",
    "This covers milestones from the 1950s...",
    "Students explore daily life AI uses...",
    "A reflection on ethical dilemmas in AI..."
  ],
  "assessments": [
    "MCQ: What defines AI?",
    "Flashcard Set: Core AI Terms",
    "Q&A: Explain supervised vs unsupervised learning",
    "MCQ: What ethical issues surround automation?"
  ]
}

Environment Variables
---------------------
OPENAI_API_KEY  - Required for LLM access via OpenAI

Key Design Highlights
---------------------
- Modular Architecture
- Centralized Pipeline
- Configurable Assessments
- Typed Models
- Future-Ready for new agents

Testing with Swagger
--------------------
Open browser: http://127.0.0.1:8000/docs

Tech Stack
-----------
- FastAPI
- OpenAI GPT
- Pydantic
- Uvicorn
- python-dotenv

Development Notes
-----------------
To add new agents:
 1. Create new folder /agent4
 2. Add agent4.py
 3. Create router under /routers/agent4_router.py
 4. Import it in main.py
 5. Optionally include in /pipeline/run chain


