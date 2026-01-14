"""
Rate limiting middleware for FastAPI
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from fastapi import Request

# Create limiter instance
# For production with multiple instances, use Redis:
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379",
    default_limits=["1000/hour"]
)

def get_rate_limit_key(request: Request) -> str:
    """
    Custom key function - can use IP, user ID, API key, etc.
    """
    # Using IP address for ratelimiting
    return get_remote_address(request)

# Exception handler for rate limit exceeded
# @app.exception_handler(RateLimitExceeded)
# async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
#     """
#     Custom handler for rate limit exceeded errors
#     """
#     response = JSONResponse(
#         status_code=429,
#         content={
#             "detail": f"Rate limit exceeded: {exc.detail}",
#             "code": "RATE_LIMIT_EXCEEDED"
#         },
#         headers={"Retry-After": str(exc.retry_after)}
#     )
#     return response