"""
Sessions for the shared password that guards the app.

Signing in swaps the password for a token of the form
`<expiry unix seconds>.<HMAC-SHA256 hex of the expiry>`. The signing key is
derived from both AUTH_SECRET and APP_PASSWORD, so changing either one ends
every session. Settings are read on each call, never at import.
"""

import hashlib
import hmac
import time
from typing import Optional

from ..config import settings

# A backstop: the browser drops the token when its tab closes.
TOKEN_LIFETIME_SECONDS = 12 * 60 * 60


def _configured_values() -> Optional[tuple[str, str]]:
    password = settings.app_password or ""
    secret = settings.auth_secret or ""
    if not password.strip() or not secret.strip():
        return None
    return password, secret


def auth_configured() -> bool:
    """True when the server has both a password and a signing secret."""
    return _configured_values() is not None


def check_password(candidate: str) -> bool:
    """True when the candidate is exactly the configured password."""
    values = _configured_values()
    if values is None:
        return False
    return hmac.compare_digest(candidate.encode(), values[0].encode())


def _signature(expiry: str, password: str, secret: str) -> str:
    key = hashlib.sha256(f"{secret}\n{password}".encode()).digest()
    return hmac.new(key, expiry.encode(), hashlib.sha256).hexdigest()


def issue_token(now: Optional[float] = None) -> str:
    """A signed session token that expires TOKEN_LIFETIME_SECONDS from now."""
    values = _configured_values()
    if values is None:
        raise ValueError("auth is not configured")
    now = time.time() if now is None else now
    expiry = str(int(now) + TOKEN_LIFETIME_SECONDS)
    return f"{expiry}.{_signature(expiry, *values)}"


def verify_token(token: Optional[str], now: Optional[float] = None) -> bool:
    """True for an unexpired token signed with the current password and secret."""
    values = _configured_values()
    if values is None or not token:
        return False
    expiry, dot, signature = token.partition(".")
    if not dot or not expiry.isdigit() or "." in signature:
        return False
    if not hmac.compare_digest(signature, _signature(expiry, *values)):
        return False
    now = time.time() if now is None else now
    return int(expiry) > now
