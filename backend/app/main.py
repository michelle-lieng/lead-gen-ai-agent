"""
FastAPI application entry point
"""

import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api.routes import (
    projects,
    leads_serp,
    leads_dataset,
    merged_results,
    enrichments,
    jobs,
    chat,
)
from .services.database_service import db_service
from .services.job_service import job_service
from .config import settings
from . import exceptions

logger = logging.getLogger(__name__)

# =========================
# App
# =========================

# Create FastAPI app
app = FastAPI(
    title="AI Lead Generator API",
    description="API for managing lead generation projects",
    version="1.0.0",
)

# =========================
# Middleware
# =========================

# Unhandled exceptions are turned into JSON *here*, inside the CORS layer,
# rather than by the `Exception` handler further down. Starlette runs that
# handler in ServerErrorMiddleware, which wraps every user middleware — so its
# 500 never passes back out through CORSMiddleware, reaches the browser with no
# Access-Control-Allow-Origin, and is discarded before the SPA can read it. The
# SPA sees a request with no response and reports it as "can't reach the
# backend", sending the user to check a server that was answering all along.
#
# Registered BEFORE CORSMiddleware on purpose: Starlette inserts each new
# middleware at the top of the stack, so the last one added is the outermost.
# Adding this one first leaves it inside CORS, where its response still gets
# the headers.
@app.middleware("http")
async def unhandled_errors_as_json(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        logger.error("UNEXPECTED ERROR on %s: %r", request.url, exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An unexpected error occurred",
                "code": "UNEXPECTED_INTERNAL_ERROR",
            },
        )


# Add CORS middleware for frontend communication.
# The React SPA calls this API directly from the browser and sends the user's
# API keys via custom headers (X-OpenAI-Key / X-Jina-Key). We must therefore
# allow those headers through preflight. `allow_credentials` is False because we
# use header-based keys (no cookies); a wildcard origin with credentials would
# be rejected by browsers and would also invalidate the `*` header allowance.
# Origins are configurable via CORS_ALLOW_ORIGINS (comma-separated); in
# production set it to the deployed frontend origin, e.g. the Vercel URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Exception handlers
# =========================


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    FastAPI validation errors (request body/query/path schema issues).
    NOTE: Avoid echoing the full request body in responses (possible sensitive data).
    """
    logger.info("Validation error on %s: %s", request.url, exc.errors())
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


@app.exception_handler(HTTPException)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    FastAPI/Starlette HTTP exceptions (explicitly raised with a status code).
    """
    logger.info("HTTP %s on %s: %s", exc.status_code, request.url, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(exceptions.AppError)
async def app_error_handler(request: Request, exc: exceptions.AppError):
    logger.warning("AppError %s on %s: %s", exc.code, request.url, str(exc))
    payload = {"detail": str(exc), "code": exc.code}
    if getattr(exc, "meta", None):
        payload["meta"] = exc.meta
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Last-resort fallback for unexpected exceptions.
    Logs full traceback, returns generic error to client.

    Anything raised by a route is caught by `unhandled_errors_as_json` above,
    which answers from inside the CORS layer. This stays as the backstop for
    the narrow case that middleware cannot reach — a failure in the middleware
    stack itself — and its response carries no CORS headers, which is why it is
    not where route errors should land.
    """
    logger.error("UNEXPECTED ERROR on %s: %r", request.url, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred",
            "code": "UNEXPECTED_INTERNAL_ERROR",
        },
    )


# =========================
# Routes / startup
# =========================


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    logger.info("🚀 Initializing database on startup")
    db_service.create_tables()
    logger.info("✅ Database initialized successfully")

    # Mark all running jobs as failed (they were left running due to server crash/shutdown)
    logger.info("🧹 Cleaning up running jobs from previous session")
    failed_count = job_service.mark_all_running_jobs_as_failed(
        error_message="Server restarted - job was running when server shut down"
    )
    if failed_count > 0:
        logger.info(f"✅ Marked {failed_count} job(s) as failed")
    else:
        logger.info("ℹ️ No running jobs to clean up")

########## DEFAULT ENDPOINTS


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "AI Lead Generator API", "status": "running"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    db_connected = db_service.check_database_connection()
    return {
        "status": "healthy" if db_connected else "unhealthy",
    }


############ PROJECT ENDPOINTS

# Include API routes
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])

########## QUERY ENDPOINTS

app.include_router(leads_serp.router, prefix="/api", tags=["serp-leads"])

########## DATASET ENDPOINTS

app.include_router(leads_dataset.router, prefix="/api", tags=["datasets"])

########## MERGED RESULTS ENDPOINTS

app.include_router(merged_results.router, prefix="/api", tags=["merged-results"])

########## ENRICHMENT ENDPOINTS

app.include_router(enrichments.router, prefix="/api", tags=["enrichments"])

########## JOB ENDPOINTS

app.include_router(jobs.router, prefix="/api", tags=["jobs"])

########## CHAT ENDPOINTS

app.include_router(chat.router, prefix="/api", tags=["chat"])
