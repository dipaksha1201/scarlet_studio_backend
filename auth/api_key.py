from fastapi import Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
import os

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)):
    expected = os.getenv("API_KEY", "dev-key")
    if not api_key or api_key != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return api_key

