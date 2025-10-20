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

## Next Steps

- Add concrete Supabase models/services under `datalayer/`.
- Scaffold feature-specific routers in `routes/` and include them in `main.py`.
- Extend `ai_scripts/` with command-line utilities to support ML/AI experimentation.
