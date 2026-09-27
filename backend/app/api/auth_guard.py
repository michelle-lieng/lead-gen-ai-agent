"""
The session guard: every /api request needs `Authorization: Bearer <token>`
from POST /api/auth/login, except the few routes a signed-out browser needs.

Registered inside CORSMiddleware, so its 401 and 503 answers still carry CORS
headers and the SPA can read them instead of reporting an unreachable server.
"""

from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse

from ..exceptions import AuthNotConfiguredError
from ..services.auth_service import auth_configured, verify_token

SESSION_REQUIRED_MESSAGE = "Your session has ended. Enter the password again."


def is_open(method: str, path: str) -> bool:
    """True for requests that need no session."""
    if method == "OPTIONS":
        return True  # CORS preflight never carries credentials
    if path != "/api" and not path.startswith("/api/"):
        return True
    if path == "/api/health":
        return True
    return method == "POST" and path.rstrip("/") == "/api/auth/login"


def bearer_token(header: Optional[str]) -> Optional[str]:
    """The token from an Authorization header, whatever the scheme's case or spacing."""
    if not header:
        return None
    scheme, _, token = header.strip().partition(" ")
    token = token.strip()
    if scheme.lower() != "bearer" or not token:
        return None
    return token


async def require_session(request: Request, call_next):
    # The path routing uses. request.url is rebuilt from the Host header, which
    # a caller can craft (e.g. "a#") to hide the path from this check.
    if is_open(request.method, request.scope["path"]):
        return await call_next(request)
    if not auth_configured():
        error = AuthNotConfiguredError()
        return JSONResponse(
            status_code=error.status_code,
            content={"detail": str(error), "code": error.code},
        )
    if not verify_token(bearer_token(request.headers.get("authorization"))):
        return JSONResponse(
            status_code=401,
            content={"detail": SESSION_REQUIRED_MESSAGE, "code": "SESSION_REQUIRED"},
        )
    return await call_next(request)
