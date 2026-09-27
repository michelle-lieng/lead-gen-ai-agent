"""
Shared FastAPI dependencies.

API keys are read from the backend's environment (see config.py):
    - OPENAI_API_KEY
    - JINA_API_KEY           (raw key, without the "jina_" prefix)
    - GOOGLE_PLACES_API_KEY  (optional; location searches only)

Routes take them through `Depends(get_api_keys)` and ask for the ones they
need with `require_*`, which names the missing env var when one is unset.
"""

from dataclasses import dataclass
from typing import Optional

from ..config import settings
from ..exceptions import ApiKeyNotConfiguredError


def _missing(name: str, env_var: str) -> ApiKeyNotConfiguredError:
    return ApiKeyNotConfiguredError(
        f"{name} API key is not set on the server. Set {env_var} in the backend's environment."
    )


@dataclass
class ApiKeys:
    """The server's API keys (any may be None)."""

    openai_api_key: Optional[str] = None
    jina_api_key: Optional[str] = None
    google_api_key: Optional[str] = None

    def require_openai(self) -> str:
        """Return the OpenAI key or raise if the server has none."""
        if not self.openai_api_key or not self.openai_api_key.strip():
            raise _missing("OpenAI", "OPENAI_API_KEY")
        return self.openai_api_key.strip()

    def require_jina(self) -> str:
        """Return the Jina key or raise if the server has none."""
        if not self.jina_api_key or not self.jina_api_key.strip():
            raise _missing("Jina", "JINA_API_KEY")
        return self.jina_api_key.strip()

    def require_google(self) -> str:
        """Return the Google Places key or raise if the server has none."""
        if not self.google_api_key or not self.google_api_key.strip():
            raise _missing("Google Places", "GOOGLE_PLACES_API_KEY")
        return self.google_api_key.strip()


def get_api_keys() -> ApiKeys:
    """FastAPI dependency: the API keys from the backend's environment."""
    return ApiKeys(
        openai_api_key=settings.openai_api_key,
        jina_api_key=settings.jina_api_key,
        google_api_key=settings.google_places_api_key,
    )
