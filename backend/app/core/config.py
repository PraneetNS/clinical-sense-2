from pydantic_settings import BaseSettings
from pydantic import field_validator, RedisDsn, AnyHttpUrl
from typing import Optional, List, Union
from enum import Enum
import os

class Environment(str, Enum):
    development = "development"
    staging = "staging"
    production = "production"

class Settings(BaseSettings):
    ENV: Environment = Environment.development
    PROJECT_NAME: str = "Clinical Documentation Assistant"
    API_V1_STR: str = "/api/v1"
    
    # Supabase (Database)
    DATABASE_URL: str
    SUPABASE_DATABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    
    # Firebase (Auth)
    FIREBASE_PROJECT_ID: str
    FIREBASE_CLIENT_EMAIL: str
    FIREBASE_PRIVATE_KEY: str
    
    # Rate Limiting
    AI_RATE_LIMIT: str = "10/minute"
    GLOBAL_RATE_LIMIT: str = "100/minute"

    # Frontend
    FRONTEND_URL: str
    
    # AI Providers (Groq Only)
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        return v or []

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: Optional[str]) -> str:
        if not v:
            raise ValueError("DATABASE_URL is required (Supabase PostgreSQL)")
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    @field_validator("FRONTEND_URL", mode="before")
    @classmethod
    def validate_frontend_url(cls, v: Optional[str]) -> str:
        if not v:
            if os.getenv("ENV") == "production":
                raise ValueError("FRONTEND_URL must be set in production")
            return "http://localhost:3000"
        return v

    @field_validator("FIREBASE_PRIVATE_KEY", mode="before")
    @classmethod
    def validate_firebase_private_key(cls, v: str) -> str:
        if v and "\\n" in v:
            return v.replace("\\n", "\n")
        return v

    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }

settings = Settings()

# Fail Fast: Strict Production Readiness Checks
if settings.ENV == Environment.production:
    missing = []
    if not settings.DATABASE_URL: missing.append("DATABASE_URL")
    if not settings.FIREBASE_PROJECT_ID: missing.append("FIREBASE_PROJECT_ID")
    if not settings.FIREBASE_CLIENT_EMAIL: missing.append("FIREBASE_CLIENT_EMAIL")
    if not settings.FIREBASE_PRIVATE_KEY: missing.append("FIREBASE_PRIVATE_KEY")
    if not settings.GROQ_API_KEY: missing.append("GROQ_API_KEY")
    
    if missing:
        raise RuntimeError(f"CRITICAL: Production deployment failed due to missing configs: {', '.join(missing)}")

    # Ensure CORS includes frontend
    if settings.FRONTEND_URL not in settings.BACKEND_CORS_ORIGINS:
        settings.BACKEND_CORS_ORIGINS.append(settings.FRONTEND_URL)
