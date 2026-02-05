from pydantic_settings import BaseSettings
from pydantic import validator, RedisDsn, AnyHttpUrl
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
    
    # Security
    JWT_SECRET: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8 # 8 days
    
    # Database
    DATABASE_URL: str
    
    # Rate Limiting
    AI_RATE_LIMIT: str = "10/minute"
    GLOBAL_RATE_LIMIT: str = "100/minute"

    # Frontend
    FRONTEND_URL: str
    
    # AI Providers
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    OPENAI_API_KEY: Optional[str] = None
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]], values: dict) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        return v or []

    @validator("JWT_SECRET", pre=True)
    def validate_jwt_secret(cls, v: Optional[str]) -> str:
        if not v:
            if os.getenv("ENV") == "production":
                raise ValueError("JWT_SECRET must be set in production")
            return "DEVELOPMENT_SECRET_REPLACE_IN_PROD"
        return v

    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v: Optional[str]) -> str:
        if not v:
            if os.getenv("ENV") == "production":
                raise ValueError("DATABASE_URL must be set in production")
            # In non-production, we still require a DATABASE_URL for this strict mode
            # unless we really want to allow local dev without it, but the prompt says 
            # "Remove all local database usage".
            raise ValueError("DATABASE_URL is required")
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    @validator("FRONTEND_URL", pre=True)
    def validate_frontend_url(cls, v: Optional[str]) -> str:
        if not v:
            if os.getenv("ENV") == "production":
                raise ValueError("FRONTEND_URL must be set in production")
            return "http://localhost:3000"
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Fail Fast: Strict Production Readiness Checks
if settings.ENV == Environment.production:
    missing = []
    if not settings.JWT_SECRET or settings.JWT_SECRET == "super-long-random-production-secret":
        missing.append("JWT_SECRET")
    if not settings.DATABASE_URL:
        missing.append("DATABASE_URL")
    if not settings.FRONTEND_URL:
        missing.append("FRONTEND_URL")
    if not settings.GROQ_API_KEY:
        missing.append("GROQ_API_KEY")
    
    if missing:
        raise RuntimeError(f"CRITICAL: Production deployment failed due to missing secrets: {', '.join(missing)}")

    # Ensure CORS includes frontend
    if settings.FRONTEND_URL not in settings.BACKEND_CORS_ORIGINS:
        settings.BACKEND_CORS_ORIGINS.append(settings.FRONTEND_URL)
