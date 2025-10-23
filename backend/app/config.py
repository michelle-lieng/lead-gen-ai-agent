"""
Configuration management for the backend
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # NO DEFAULTS, must be provided
    # Database settings
    postgresql_host: str
    postgresql_port: int
    postgresql_user: str
    postgresql_password: str
    postgresql_database: str
    
    # API Keys
    openai_api_key: str
    tavily_api_key: str
    serp_api_key: str
    jina_api_key: str
    google_maps_api_key: str
    
    # App settings
    log_level: str = Field(default="INFO") # Only log level has a default
    
    # tells pydantic how to load the file
    model_config = {
        "env_file": "../.env",  # Look in project root, not backend directory
        "env_file_encoding": "utf-8"
    }

# Global settings instance
settings = Settings()
