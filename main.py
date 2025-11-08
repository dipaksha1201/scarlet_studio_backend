# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import agent1_router, agent2_router, agent3_router, pipeline_router

app = FastAPI(title="AI Tutor Backend", version="1.0.0")

# Allow frontend access (React app, localhost, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers for each agent
app.include_router(agent1_router.router)
app.include_router(agent2_router.router)
app.include_router(agent3_router.router)
app.include_router(pipeline_router.router)

@app.get("/")
def home():
    return {"message": "AI Tutor Backend is running 🚀"}
