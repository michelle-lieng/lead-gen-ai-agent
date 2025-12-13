"""
FastAPI application entry point
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import projects, leads_serp, leads_dataset, merged_results
from .services.database_service import db_service

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

