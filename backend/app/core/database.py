from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

if DATABASE_URL.startswith("sqlite"):
    _engine_kwargs = {"connect_args": {"check_same_thread": False}}
else:
    _engine_kwargs = {"pool_size": settings.DB_POOL_SIZE, "max_overflow": settings.DB_MAX_OVERFLOW}

engine = create_engine(
    DATABASE_URL,
    # Also covers connections left idle while a Lambda container was frozen.
    pool_pre_ping=True,
    **_engine_kwargs,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a request-scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
