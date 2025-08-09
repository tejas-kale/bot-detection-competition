"""Configuration management for the bot detection project."""

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Environment
    environment: str = Field(default="dev", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # GCP Configuration
    gcp_project_id: str = Field(default="", env="GCP_PROJECT_ID")
    gcp_bucket_name: str = Field(default="", env="GCP_BUCKET_NAME")
    google_application_credentials: Optional[str] = Field(None, env="GOOGLE_APPLICATION_CREDENTIALS")
    
    # Kaggle Configuration
    kaggle_username: Optional[str] = Field(None, env="KAGGLE_USERNAME")
    kaggle_key: Optional[str] = Field(None, env="KAGGLE_KEY")
    
    # Data Pipeline Configuration
    data_version_prefix: str = Field(default="v", env="DATA_VERSION_PREFIX")
    
    # Prefect Configuration
    prefect_api_url: str = Field(default="http://127.0.0.1:4200/api", env="PREFECT_API_URL")
    
    class Config:
        env_file = None  # Will be set dynamically
        case_sensitive = False


def get_settings(environment: str = "dev") -> Settings:
    """Get settings for the specified environment."""
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / f".env.{environment}"
    
    # Update the Config class to use the correct env file
    Settings.Config.env_file = str(env_file) if env_file.exists() else None
    
    return Settings()


def setup_kaggle_credentials(settings: Settings) -> None:
    """Set up Kaggle API credentials."""
    if settings.kaggle_username and settings.kaggle_key:
        os.environ["KAGGLE_USERNAME"] = settings.kaggle_username
        os.environ["KAGGLE_KEY"] = settings.kaggle_key


def setup_gcp_credentials(settings: Settings) -> None:
    """Set up GCP credentials."""
    if settings.google_application_credentials:
        credentials_path = Path(__file__).parent.parent.parent / settings.google_application_credentials
        if credentials_path.exists():
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(credentials_path)
        else:
            raise FileNotFoundError(f"GCP credentials file not found: {credentials_path}")