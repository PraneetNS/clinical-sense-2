from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from ..core.config import settings

# ---------------------------------------------------------------------------
# Engine — optimised for Render cloud PostgreSQL
# ---------------------------------------------------------------------------
_connect_args = {
    "connect_timeout": 10,
    "options": "-c statement_timeout=30000",   # 30s hard limit per statement
}

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,          # Recycle connections before PG idle timeout
    pool_pre_ping=True,         # Drop stale connections automatically
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency — yields a session, always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
