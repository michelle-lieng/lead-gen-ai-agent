"""
Simple settings: env vars validated via pydantic-settings, plus a small
config.yaml presence check. One place to load .env and validate quickly.
"""
from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import yaml

class ConfigSettings(BaseModel):
    postgresql_database: str

class Settings(BaseSettings):
    # Database connection (env)
    POSTGRESQL_HOST: str
    POSTGRESQL_PORT: int
    POSTGRESQL_USER: str
    POSTGRESQL_PASSWORD: str
    POSTGRESQL_INITIAL_DATABASE: str

    # External APIs (env)
    SERP_API_KEY: str
    JINA_API_KEY: str

    model_config = SettingsConfigDict(env_file=None, extra="ignore")


def _validate_config_yaml(path_str: str) -> None:
    path = Path(path_str)
    if not path.exists():
        raise ValueError(f"Configuration file not found at {path.resolve()}")
    
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception as exc:
        raise ValueError(f"Failed to read configuration file {path}: {exc}") from exc
    
    db_name = data.get("postgresql_database")
    if not db_name or str(db_name).strip() == "":
        raise ValueError(f"Add 'postgresql_database' to {path}")


def load_settings() -> tuple[Settings, ConfigSettings]:
    # Load .env once and validate env vars
    load_dotenv()
    settings = Settings()  # validates env on init
    
    # Validate YAML config separately
    _validate_config_yaml("config.yaml")
    with Path("config.yaml").open("r", encoding="utf-8") as f:
        yaml_data = yaml.safe_load(f) or {}
    config = ConfigSettings(**yaml_data)
    
    return settings, config


