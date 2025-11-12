# Scarlet Studio Backend (local workspace)

This repo contains a small backend utility for generating multiple-choice quizzes from simple module descriptions.

Project root (working directory)
- /Users/madhusiddharthsuthagar/Documents/python/scarlet_studio_backend

Key files
- main.py — CLI driver that triggers quiz generation.
- generation/module.py — QuizGenerator and pydantic models for validation.
- generation/content.py — Reads data/static_module.json, calls the generator, writes data/quiz_output.json.
- api/qa_evaluation.py — Interactive CLI to run quizzes and record performance.
- api/qa_evaluation_api.py — Small HTTP API server to trigger CLI runs and serve performance data.
- data/static_module.json — Input module definitions (id + description).
- data/quiz_output.json — Generated quizzes are written here.
- data/performance.json — Saved quiz attempts (created after running quizzes).
- requirements.txt — Python dependencies to install in your virtual environment.
- .env — Store GEMINI_API_KEY here (not committed).

Quick start (local)
1. Create and activate virtualenv:
   python -m venv .venv
   source .venv/bin/activate

2. Install dependencies:
   pip install -r requirements.txt

3. Add your Google Generative API key to a `.env` file at the repo root (only needed for generation):
   GEMINI_API_KEY=your_key_here

4. Generate quizzes (optional if quiz_output.json already exists):
   python main.py

API (local)
- Start server:
  python api/qa_evaluation_api.py
  By default the server listens at: http://127.0.0.1:8000

- Endpoints:
  - GET /               → Health check: {"status":"ok"}
  - GET /performance    → Returns the contents of data/performance.json
  - POST /run           → Attempts to run the interactive CLI (api/qa_evaluation.py). If the server process has access to /dev/tty it will spawn the CLI attached to the terminal where the server was started; otherwise it will try to invoke the CLI function directly (may not be interactive).
  - POST /simulate      → Accepts a JSON array of performance entries and appends them to data/performance.json (useful for testing).

- Example curl commands:
  - Health:
    curl http://127.0.0.1:8000/
  - Get performance:
    curl http://127.0.0.1:8000/performance
  - Trigger interactive run (server must have TTY access):
    curl -X POST http://127.0.0.1:8000/run
  - Simulate appending performance entries:
    curl -X POST -H "Content-Type: application/json" \
      -d '[{"timestamp":"2025-11-12T00:00:00Z","module":"networks","question":"...","selected_index":1,"correct_index":2,"correct":false,"explanation":"..."}]' \
      http://127.0.0.1:8000/simulate

Interactive CLI (direct)
- If /run cannot attach to a TTY, run the CLI directly:
  python api/qa_evaluation.py
- The CLI will:
  - Read quizzes from data/quiz_output.json
  - Prompt you to pick module(s)
  - Show each question and options, accept answers, display correct answer + explanation
  - Append attempts to data/performance.json

Where results are saved
- data/performance.json — Each saved entry contains timestamp, module, question, selected_index, correct_index, correct (bool), and explanation.

Troubleshooting
- If POST /run returns an error about TTY, start the server in a terminal and run the curl command from another terminal, or run the CLI directly with python api/qa_evaluation.py.
- Ensure you run commands from the project root so relative data paths resolve correctly.
- If performance.json isn't updated, check server logs/console output for errors.

Notes
- Keep your API key private (add .env to .gitignore).
- The interactive run writes user responses — review the performance file before sharing.
