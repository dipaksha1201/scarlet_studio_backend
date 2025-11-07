# Scarlet Studio Backend Template

Starter layout for the Scarlet Studio backend, built with FastAPI and Supabase.
Share this repo with new teammates so everyone begins with the same conventions.

## Getting Started

1. Create a virtual environment and install dependencies (e.g. `fastapi`, `uvicorn`, `supabase`).
2. Export Supabase credentials. The app expects `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`.
3. Run the FastAPI server with `uvicorn main:app --reload`.

## Directory Guide

- `main.py` &ndash; FastAPI entrypoint. Registers application routes and shared middleware.
- `routes/` &ndash; Organise API endpoints here. Every new router module must be included in `main.py`.
- `datalayer/` &ndash; Supabase client bootstrap and base service classes for data access logic.
- `ai_scripts/` &ndash; Place executable Python scripts related to AI workflows or offline jobs.
- `auth/` &ndash; Placeholder for future authentication helpers and policies.

## Assessment Designer Service

This repo includes a simple Assessment Designer API that can:
- Generate quizzes, flashcards and Q&A pairs from module content.
- Return module lists and paragraphs for content creation.
- Evaluate assessment responses.

Authentication: endpoints expect an `X-API-Key` header. For development set environment variable `API_KEY` or use default `dev-key`.

Run:
1. python -m venv .venv && source .venv/bin/activate
2. pip install fastapi uvicorn
3. export API_KEY=dev-key
4. uvicorn main:app --reload

OpenRouter integration:
- Optionally provide `OPENROUTER_API_KEY` in a `.env` file at the repo root to enable future model-driven refinements.
- The services detect the presence of the key and annotate outputs. Replace local heuristics in services/assessment_designer.py with calls to OpenRouter if you want richer generation.

Performance persistence:
- Module-level performance is stored at `data/performance.json`. Generated items include a `source_index` that ties questions/flashcards/QA pairs back to paragraph indices.
- When you POST to /assessments/evaluate include `module_id` in the body to persist attempts/correct counts. The generator prioritizes items with lower correct rate when creating new assessments.

Example .env:
- Copy `.env.example` to `.env` and set your keys:
  API_KEY=dev-key
  OPENROUTER_API_KEY=...

Available endpoints (protected by X-API-Key):
- GET /modules
- POST /modules
- GET /modules/{module_id}/content
- POST /assessments/generate  (body: module_id, type: "quiz"|"flashcards"|"qa")
- POST /assessments/evaluate  (body: answers + the original assessment)

Static input:
- data/static_modules.json contains sample modules used by the agent.

Git:
- A helper script git_push.sh is included to push changes (you must configure remote).

## Next Steps

- Integrate OpenRouter calls in services/assessment_designer.py if you want to generate content using a remote model.
- Add concrete Supabase models/services under `datalayer/`.
- Scaffold feature-specific routers in `routes/` and include them in `main.py`.
- Extend `ai_scripts/` with command-line utilities to support ML/AI experimentation.
