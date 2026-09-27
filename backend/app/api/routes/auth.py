"""
Signing in with the shared password, and which API keys the server has.
"""
import asyncio

from fastapi import APIRouter

from ...config import settings
from ...exceptions import AuthNotConfiguredError, InvalidPasswordError
from ...models.schemas import LoginRequest, LoginResponse, ServerKeysResponse
from ...services.auth_service import auth_configured, check_password, issue_token

router = APIRouter()

# Slows guessing; there is no lockout.
FAILED_LOGIN_DELAY_SECONDS = 1.0


def _is_set(value) -> bool:
    return bool((value or "").strip())


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Swap the shared password for a session token."""
    if not auth_configured():
        raise AuthNotConfiguredError()
    if not check_password(request.password):
        await asyncio.sleep(FAILED_LOGIN_DELAY_SECONDS)
        raise InvalidPasswordError()
    return LoginResponse(token=issue_token())


@router.get("/status", response_model=ServerKeysResponse)
def status():
    """Which API keys the server has, so the app knows what can run."""
    return ServerKeysResponse(
        openai=_is_set(settings.openai_api_key),
        jina=_is_set(settings.jina_api_key),
        google=_is_set(settings.google_places_api_key),
    )
