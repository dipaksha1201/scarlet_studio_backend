# utils/env_loader.py
from dotenv import load_dotenv
import os

def get_env(name: str, required: bool = True, default: str | None = None) -> str | None:
    load_dotenv()
    val = os.getenv(name, default)
    if required and not val:
        raise ValueError(f"Missing required environment variable: {name}")
    return val
