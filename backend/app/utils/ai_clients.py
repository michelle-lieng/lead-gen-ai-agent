"""
Helpers for building per-request OpenAI clients/models from a user-supplied key.

Previously the OpenAI key was global (``set_default_openai_key`` + a cached
client). With per-user keys we must build clients per request so concurrent
requests never share or clobber each other's credentials. For the OpenAI Agents
SDK we attach an explicit ``AsyncOpenAI`` client to an ``OpenAIResponsesModel``
instead of relying on the process-global default key.
"""

import openai

try:  # openai-agents re-exports this at the top level in 0.6.x
    from agents import OpenAIResponsesModel
except ImportError:  # pragma: no cover - fallback for other versions
    from agents.models.openai_responses import OpenAIResponsesModel

DEFAULT_MODEL = "gpt-5-mini"


def build_openai_client(openai_api_key: str) -> openai.OpenAI:
    """Build a synchronous OpenAI client for direct Responses API calls."""
    return openai.OpenAI(api_key=openai_api_key)


def build_agent_model(
    openai_api_key: str, model: str = DEFAULT_MODEL
) -> OpenAIResponsesModel:
    """
    Build a per-request Agents-SDK model bound to the caller's key.

    Passing this as an Agent's ``model`` keeps each run isolated to its own key
    (concurrency-safe), unlike the global ``set_default_openai_key``.
    """
    async_client = openai.AsyncOpenAI(api_key=openai_api_key)
    return OpenAIResponsesModel(model=model, openai_client=async_client)
