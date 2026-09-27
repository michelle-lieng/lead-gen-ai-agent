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
    
    # Access: one shared password guards the whole API. Sessions are signed
    # with AUTH_SECRET; changing either value signs everyone out. With either
    # unset, every guarded route answers 503 rather than running open.
    app_password: Optional[str] = None
    auth_secret: Optional[str] = None

    # API Keys, read from the environment. The server boots without them, but
    # searches and columns need OpenAI and Jina; Google Places is optional
    # (location searches fall back to the web without it).
    openai_api_key: Optional[str] = None
    jina_api_key: Optional[str] = None
    google_places_api_key: Optional[str] = None

    debug: bool = Field(default=False)

    # App settings
    log_level: str = Field(default="INFO") # Only log level has a default

    # CORS: comma-separated list of allowed origins for the browser SPA.
    # Defaults to "*" for local dev; in production set this to the deployed
    # frontend origin(s), e.g. "https://your-app.vercel.app".
    cors_allow_origins: str = Field(default="*")

    @property
    def cors_allow_origins_list(self) -> list[str]:
        """Parse the comma-separated origins into a clean list."""
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]

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
