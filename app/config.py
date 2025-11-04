# app/config.py
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Health Tracker API"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(default=["*"])
    
    # Firebase
    FIREBASE_CREDENTIALS_PATH: str = "service-account.json"
    FIREBASE_API_KEY: str = Field(..., env="FIREBASE_API_KEY")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print(f"FIREBASE_CREDENTIALS_PATH: {self.FIREBASE_CREDENTIALS_PATH}")

    # JWT Settings
    SECRET_KEY: str = "development_secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Notification Service
    ENABLE_NOTIFICATIONS: bool = True
    FCM_API_KEY: Optional[str] = None

    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
