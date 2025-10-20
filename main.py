from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from datalayer import init_supabase_client

logger = logging.getLogger(__name__)


def _bootstrap_supabase() -> None:
    """
    Initialise the shared Supabase client if credentials are present.

    Missing credentials are tolerated so the app can still start during local
    scaffolding. Once environment variables are configured, the client will be
    ready for dependency injection across services.
    """
    try:
        init_supabase_client()
        logger.info("Supabase client initialised.")
    except ValueError as exc:
        logger.warning("Supabase client skipped: %s", exc)


def register_routes(app: FastAPI) -> None:
    """
    Import and include routers here.

    Example:

        from routes import users
        app.include_router(users.router, prefix=\"/users\", tags=[\"Users\"])
    """
    # No routers yet—add them here as the project grows.


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Lifecycle management for the FastAPI application."""
    _bootstrap_supabase()
    register_routes(app)
    yield


app = FastAPI(
    title="Scarlet Studio Backend",
    description="FastAPI + Supabase starter for Scarlet Studio services.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["Health"])
async def healthcheck() -> dict[str, str]:
    """Simple endpoint that reports service status."""
    return {"status": "ok"}
