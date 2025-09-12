from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Business Dashboard"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./business.db")
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    EXTERNAL_API_KEY: Optional[str] = os.getenv("EXTERNAL_API_KEY")
    EXTERNAL_API_URL: Optional[str] = os.getenv("EXTERNAL_API_URL")
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()