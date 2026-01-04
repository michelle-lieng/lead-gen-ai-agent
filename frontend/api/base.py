"""
Base API client configuration and shared utilities
"""

import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuration
# Read from environment variable (set by Docker) or default to localhost for local dev
BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
# Default timeout: 10 minutes (600 secs) for lead extraction operations which can process many URLs sequentially
# Each URL can take 10-30 seconds with AI processing + scraping, so with 50 URLs this could take 8+ minutes
TIMEOUT = 600

# Create one shared session for connection reuse
_session = requests.Session()

# Add retry logic
retry = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=(502, 503, 504),
    allowed_methods=("GET", "POST", "PUT", "DELETE"),
    raise_on_status=False,
)
adapter = HTTPAdapter(max_retries=retry)
_session.mount("http://", adapter)
_session.mount("https://", adapter)
_session.headers.update({"Accept": "application/json"})


def _request(method: str, path: str, json_data=None, stream=False, files=None, form_data=None):
    """Make HTTP request - returns response, raises Exception for HTTP errors, or returns None for network errors"""
    try:
        url = f"{BASE_URL}{path}"
        
        # Make the request
        if files is not None:
            response = _session.request(method, url, files=files, data=form_data, timeout=TIMEOUT, stream=stream)
        else:
            response = _session.request(method, url, json=json_data, timeout=TIMEOUT, stream=stream)
        
    except requests.exceptions.RequestException:
        # Network/connection error - return None
        return None
    
    # Success - return response
    if response.status_code >= 200 and response.status_code < 300:
        return response
    
    # HTTP error - extract error details and raise
    error_detail = f'HTTP {response.status_code} error'
    error_code = None
    try:
        error_data = response.json()
        error_detail = error_data.get('detail', error_detail)
        error_code = error_data.get('code')
    except:
        pass  # If JSON parsing fails, use defaults above
    
    exception = Exception(error_detail)
    exception.error_code = error_code
    exception.status_code = response.status_code
    raise exception