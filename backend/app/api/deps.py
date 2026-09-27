"""
Shared FastAPI dependencies.

API keys are supplied per-request by the frontend via HTTP headers instead of
being configured server-side:
    - X-OpenAI-Key: the user's OpenAI API key
    - X-Jina-Key:   the user's Jina API key (raw key, without the "jina_" prefix)
    - X-Google-Key: the user's Google Places key (optional; location searches only)

These are threaded into the AI/scraping services so each request uses the
caller's own credentials.
"""

from dataclasses import dataclass
from typing import Optional

from fastapi import Header

from ..exceptions import ApiKeyNotConfiguredError


@dataclass
class ApiKeys:
    """Per-request API keys extracted from headers (either may be None)."""

    openai_api_key: Optional[str] = None
    jina_api_key: Optional[str] = None
    google_api_key: Optional[str] = None

    def require_openai(self) -> str:
        """Return the OpenAI key or raise if the caller didn't supply one."""
        if not self.openai_api_key or not self.openai_api_key.strip():
            raise ApiKeyNotConfiguredError(
                "OpenAI API key not provided. Enter your OpenAI API key in the app."
            )
        return self.openai_api_key.strip()

    def require_jina(self) -> str:
        """Return the Jina key or raise if the caller didn't supply one."""
        if not self.jina_api_key or not self.jina_api_key.strip():
            raise ApiKeyNotConfiguredError(
                "Jina API key not provided. Enter your Jina API key in the app."
            )
        return self.jina_api_key.strip()

    def require_google(self) -> str:
        """Return the Google Places key or raise if the caller didn't supply one."""
        if not self.google_api_key or not self.google_api_key.strip():
            raise ApiKeyNotConfiguredError(
                "Google Places API key not provided. Add it under API keys."
            )
        return self.google_api_key.strip()


def get_api_keys(
    x_openai_key: Optional[str] = Header(default=None, alias="X-OpenAI-Key"),
    x_jina_key: Optional[str] = Header(default=None, alias="X-Jina-Key"),
    x_google_key: Optional[str] = Header(default=None, alias="X-Google-Key"),
) -> ApiKeys:
    """FastAPI dependency that reads the user's API keys from request headers."""
    return ApiKeys(
        openai_api_key=x_openai_key,
        jina_api_key=x_jina_key,
        google_api_key=x_google_key,
    )
