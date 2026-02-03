from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .core.exceptions import AppError, app_error_handler, general_exception_handler
from .db.session import engine, SessionLocal
from .api.endpoints import auth, notes, patients, clinical, tasks
from .models import Base
from .core.ratelimit import limiter
from .core.config import Environment

from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from starlette.middleware.base import BaseHTTPMiddleware
from .core.logging import logger, request_id_contextvar
import uuid

# Tables are managed by Alembic migrations
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Clinical Documentation Assistant - Secure AI restructuring for clinical notes.",
    docs_url=None if settings.ENV == Environment.production else "/docs",
    redoc_url=None if settings.ENV == Environment.production else "/redoc",
)

from fastapi.staticfiles import StaticFiles
import os
if not os.path.exists("uploads"):
    os.makedirs("uploads")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Rate Limiting Setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_contextvar.set(request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Limit payload size to 10MB
class LimitUploadSize(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.method == "POST":
            if "content-length" in request.headers:
                if int(request.headers["content-length"]) > 10 * 1024 * 1024:
                    return JSONResponse(status_code=413, content={"detail": "Request too large"})
        return await call_next(request)

app.add_middleware(LimitUploadSize)

# Exception Handlers
@app.exception_handler(AppError)
async def app_error_exception_handler(request, exc):
    return await app_error_handler(request, exc)

@app.exception_handler(Exception)
async def universal_exception_handler(request, exc):
    from sqlalchemy.exc import SQLAlchemyError
    if isinstance(exc, SQLAlchemyError):
        logger.error(f"Database Error: {str(exc)}")
        return await app_error_handler(request, AppError("Database service is currently unavailable.", status_code=503))
    
    logger.error(f"Unhandled Exception: {str(exc)}")
    return await general_exception_handler(request, exc)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    try:
        # Check database connection
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {
            "status": "healthy",
            "environment": settings.ENV,
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "detail": "Database connection failed"}
        )

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.PROJECT_NAME} in {settings.ENV} mode")
    if settings.ENV == Environment.production:
        logger.info(f"CORS Origins: {settings.BACKEND_CORS_ORIGINS}")

@app.get("/")
def read_root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "environment": settings.ENV,
        "docs": "Internal API" if settings.ENV == Environment.production else "/docs"
    }

# Include Routers
app.include_router(auth.router, prefix=settings.API_V1_STR + "/auth", tags=["auth"])
app.include_router(notes.router, prefix=settings.API_V1_STR + "/notes", tags=["notes"])
app.include_router(patients.router, prefix=settings.API_V1_STR + "/patients", tags=["patients"])
# Mount clinical endpoints at /patients to match hierarchy (e.g. /patients/{id}/admissions)
app.include_router(clinical.router, prefix=settings.API_V1_STR + "/patients", tags=["clinical"])
app.include_router(tasks.router, prefix=settings.API_V1_STR + "/tasks", tags=["tasks"])

# Development entry point (only runs when executed directly, not when imported by gunicorn)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
