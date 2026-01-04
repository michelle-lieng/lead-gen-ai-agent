"""
FastAPI application entry point
"""
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import projects, leads_serp, leads_dataset, merged_results, enrichments
from .services.database_service import db_service
from . import exceptions

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Lead Generator API",
    description="API for managing lead generation projects",
    version="1.0.0"
)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    """
    Universal exception handler for all errors.
    If exception has status_code/code attributes, uses them. Otherwise returns 500.
    """
    status_code = getattr(exc, "status_code", 500)
    error_code = getattr(exc, "code", "UNEXPECTED_INTERNAL_ERROR")
    
    # For custom exceptions, show the message. For unexpected ones, hide details for security
    if hasattr(exc, "code"):
        error_message = str(exc)
        logger.error(f"{error_code}: {error_message}")
    else:
        # Log with full stack trace for unexpected errors
        logger.error(f"🚨🚨🚨 UNEXPECTED ERROR! {error_code}: {exc}", exc_info=True)
        error_message = "An unexpected error occurred"
    
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": error_message,
            "code": error_code
        }
    )

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    logger.info("🚀 Initializing database on startup")
    db_service.create_tables()
    logger.info("✅ Database initialized successfully")

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

