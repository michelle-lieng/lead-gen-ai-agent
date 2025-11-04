"""
FastAPI application entry point
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import projects, leads_serp, leads_dataset
from .services.database_service import db_service

# Configure logging
logging.basicConfig(level=logging.INFO)

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
    try:
        # Test database connection first
        if not db_service.check_database_connection():
            raise Exception("Database connection failed")
        
        # Create tables if they don't exist
        db_service.create_tables()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        # Don't crash the app, but log the error
        # The app can still run, but database operations will fail

########## DEFAULT ENDPOINTS

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "AI Lead Generator API", "status": "running"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        db_connected = db_service.check_database_connection()
        return {
            "status": "healthy" if db_connected else "unhealthy",
            "database": "connected" if db_connected else "disconnected",
            "timestamp": "2024-01-01T00:00:00Z"  # You can add actual timestamp if needed
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e)
        }

############ PROJECT ENDPOINTS

# Include API routes
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])

########## QUERY ENDPOINTS

app.include_router(leads_serp.router, prefix="/api", tags=["queries"])

########## DATASET ENDPOINTS

app.include_router(leads_dataset.router, prefix="/api", tags=["datasets"])
