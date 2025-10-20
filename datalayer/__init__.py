"""
Data layer bootstrap utilities.

This module centralises Supabase client configuration and exposes a base class
for service objects that interact with the database. Import the helpers below
from your services to keep Supabase initialisation consistent across the app.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Optional

_supabase_client: Optional["Client"] = None

if TYPE_CHECKING:  # pragma: no cover - only for static analysis
    from supabase import Client  # type: ignore


def init_supabase_client(
    url: Optional[str] = None,
    key: Optional[str] = None,
) -> "Client":
    """
    Initialise and cache a Supabase client instance.

    Parameters
    ----------
    url:
        Supabase project URL. Falls back to the SUPABASE_URL environment variable.
    key:
        Supabase service role key. Falls back to SUPABASE_SERVICE_KEY environment variable.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    resolved_url = url or os.getenv("SUPABASE_URL")
    resolved_key = key or os.getenv("SUPABASE_SERVICE_KEY")
    if not resolved_url or not resolved_key:
        raise ValueError(
            "Supabase client initialisation failed. "
            "Provide url/key arguments or set SUPABASE_URL and SUPABASE_SERVICE_KEY."
        )

    from supabase import create_client  # type: ignore

    _supabase_client = create_client(resolved_url, resolved_key)
    return _supabase_client


def get_supabase_client() -> "Client":
    """Return the cached Supabase client, ensuring init_supabase_client was called."""
    if _supabase_client is None:
        raise RuntimeError(
            "Supabase client not initialised. Call init_supabase_client() during startup."
        )
    return _supabase_client


class BaseService:
    """
    Base class for data layer services.

    Subclasses should set `self.supabase` and add shared helpers for querying
    Supabase tables. Keeping a common base makes it easy to expand with logging,
    tracing, or other cross-cutting concerns later.
    """

    def __init__(self, client: Optional["Client"] = None) -> None:
        self.supabase = client or get_supabase_client()
