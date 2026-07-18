"""
Base API client configuration and shared utilities
"""
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, Union, List

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# =========================
# Configuration
# =========================
BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
# Render private networking supplies a scheme-less "host:port"; add http:// so
# requests can build a valid URL. (localhost default already has a scheme.)
if not BASE_URL.startswith(("http://", "https://")):
    BASE_URL = f"http://{BASE_URL}"
TIMEOUT = 600

# =========================
# HTTP Session Setup with Retry Logic
# =========================

# Create a persistent HTTP session (reuses TCP connections for better performance)
_session = requests.Session()

# Configure automatic retry logic for failed requests
retry = Retry(
    total=3,                                      # Retry up to 3 times
    backoff_factor=0.5,                           # Wait 0.5s, then 1s, then 2s between retries
    status_forcelist=(502, 503, 504),             # Retry on these HTTP status codes (server errors)
    allowed_methods=("GET", "POST", "PUT", "DELETE"),  # Which HTTP methods to retry
    raise_on_status=False,                        # Don't raise exception on bad status (we handle it manually)
)

# Attach retry logic to the session via an adapter
adapter = HTTPAdapter(max_retries=retry)
_session.mount("http://", adapter)   # Apply to HTTP URLs
_session.mount("https://", adapter)  # Apply to HTTPS URLs

# Set default header to request JSON responses
_session.headers.update({"Accept": "application/json"})

# =========================
# Custom Exception Classes
# =========================

@dataclass
class ApiError(Exception):
    """
    Raised when the backend API returns an error response (4xx or 5xx status).
    
    This matches the error format from your backend's exception handlers:
    - RequestValidationError: detail will be a list of field errors
    - AppError: detail is string, code is your custom error code (e.g., "PROJECT_NOT_FOUND")
    - HTTPException: detail can be string or dict
    """
    status_code: int                           # HTTP status code (404, 400, 500, etc.)
    detail: Union[str, List[Any]]              # Error message or list of validation errors
    code: Optional[str] = None                 # Custom error code from backend (e.g., "PROJECT_NOT_FOUND")
    meta: Optional[Dict[str, Any]] = None      # Additional error metadata from backend
    url: Optional[str] = None                  # The URL that was called

    def __str__(self) -> str:
        """Returns a human-readable error message"""
        if isinstance(self.detail, str):
            return self.detail
        return f"HTTP {self.status_code} error"

class NetworkError(Exception):
    """
    Raised when we can't reach the backend at all.
    Examples: connection refused, timeout, DNS failure, no internet.
    This is different from ApiError (where we got a response, just an error response).
    """
    pass

# =========================
# Core API Request Function
# =========================

def _request(method: str, path: str, json_data=None, stream=False, files=None, form_data=None):
    """
    Core function that makes HTTP requests to the backend API.
    
    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        path: API endpoint path (e.g., "/api/projects/5")
        json_data: Python dict to send as JSON body
        stream: If True, response is streamed (for large files)
        files: File uploads (multipart/form-data)
        form_data: Form data to send with files
    
    Returns:
        requests.Response object if successful (2xx status)
    
    Raises:
        NetworkError: If we can't connect to the backend
        ApiError: If backend returns an error (4xx, 5xx)
    """
    # Build full URL (e.g., "http://localhost:8000/api/projects")
    url = f"{BASE_URL}{path}"

    # ===== Step 1: Make the HTTP request =====
    try:
        # Handle file uploads differently (multipart/form-data)
        if files is not None:
            response = _session.request(
                method, url, files=files, data=form_data, timeout=TIMEOUT, stream=stream
            )
        # Normal requests (JSON body)
        else:
            response = _session.request(
                method, url, json=json_data, timeout=TIMEOUT, stream=stream
            )
    except requests.exceptions.RequestException as e:
        # Network-level error (can't reach server at all)
        raise NetworkError(f"Network error calling {url}: {e}") from e

    # ===== Step 2: Check if request was successful =====
    # Status codes 200-299 are success
    if 200 <= response.status_code < 300:
        return response  # Success! Return response to caller

    # ===== Step 3: Handle error response =====
    # If we get here, backend returned an error (4xx or 5xx)
    
    # Default error message
    detail: Any = f"HTTP {response.status_code} error"
    code = None
    meta = None

    # Try to parse the error response JSON from backend
    try:
        data = response.json()
        # Extract fields that match your backend's exception handlers:
        # - detail: error message or validation errors list
        # - code: custom error code (e.g., "PROJECT_NOT_FOUND")
        # - meta: additional error context
        detail = data.get("detail", detail)
        code = data.get("code")
        meta = data.get("meta")
    except ValueError:
        # Response wasn't JSON (rare), use plain text
        detail = response.text or detail

    # Raise ApiError with all the error information
    raise ApiError(
        status_code=response.status_code,
        detail=detail,
        code=code,
        meta=meta,
        url=url,
    )