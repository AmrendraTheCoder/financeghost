"""
FinanceGhost Configuration
Loads environment variables and provides app settings
"""

import os
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App Configuration
    app_name: str = "FinanceGhost Autonomous"
    app_version: str = "0.1.0"
    app_env: str = Field(default="development")
    debug: bool = Field(default=False)
    
    # OpenAI Configuration
    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-4o-mini")
    
    # Optional: Google Cloud / AI Studio Configuration
    google_api_key: Optional[str] = Field(default="")
    google_cloud_project: Optional[str] = Field(default=None)
    google_application_credentials: Optional[str] = Field(default=None)
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///./financeghost.db")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    
    # OCR Configuration
    tesseract_cmd: Optional[str] = Field(default=None)  # Path to tesseract if not in PATH
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Convenience instance
settings = get_settings()
