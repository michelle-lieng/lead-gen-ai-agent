"""
Configuration management for the backend
"""
import logging
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # Database settings
    # Either provide a full DATABASE_URL (e.g. Render/managed Postgres) OR the
    # individual POSTGRESQL_* fields (local dev / docker-compose). If database_url
    # is set it takes precedence (see database_service.py).
    database_url: Optional[str] = None
    postgresql_host: Optional[str] = None
    postgresql_port: Optional[int] = None
    postgresql_user: Optional[str] = None
    postgresql_password: Optional[str] = None
    postgresql_database: Optional[str] = None
    
    # API Keys
    # Optional: keys are now supplied per-request by the frontend (via the
    # X-OpenAI-Key / X-Jina-Key headers) instead of being required server-side.
    # They remain here only as an optional fallback so the server still boots
    # without them.
    openai_api_key: Optional[str] = None
    jina_api_key: Optional[str] = None

    debug: bool = Field(default=False)
    
    # App settings
    log_level: str = Field(default="INFO") # Only log level has a default
    
    def configure_logging(self):
        """Configure logging based on settings."""
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()), #returns e.g. logging.INFO
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    # tells pydantic how to load the file
    model_config = {
        "env_file": ".env",  # Look in backend directory
        "env_file_encoding": "utf-8"
    }

# Global settings instance
settings = Settings()
settings.configure_logging() # Sets up logging with whatever level set in settings
