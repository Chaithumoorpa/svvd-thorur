"""
Test configuration.

Tests run against a real PostgreSQL database, not SQLite: the schema uses
Postgres-only types (ARRAY roles, native enums, UUID), and the schema under test
is built by running the Alembic migrations, so a missing migration fails the
suite instead of only failing in production.

Set TEST_DATABASE_URL to point at another server/database. The default matches
the docker-compose credentials and a separate `templedb_test` database, which is
created automatically if the user is allowed to (CREATEDB).
"""
import os
import uuid
from pathlib import Path

# --- Environment must be set BEFORE the app (and its settings) is imported ----
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://templeuser:templepass@localhost:5432/templedb_test",
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("SECRET_KEY", "test-only-secret-key-not-for-production-0123456789")
os.environ["ENV"] = "development"
os.environ.setdefault("LOG_LEVEL", "WARNING")

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _ensure_test_database() -> None:
    url = make_url(TEST_DATABASE_URL)
    admin_engine = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            exists = conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": url.database}
            )
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    finally:
        admin_engine.dispose()


def alembic_config() -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    return cfg


_ensure_test_database()

from app.main import app  # noqa: E402  (after env setup)
from app.models.base import Base  # noqa: E402
from app.utils.dependencies import get_db  # noqa: E402
from app.core.security import create_access_token, hash_password  # noqa: E402
from app.models.user import User  # noqa: E402
from app import models as _models  # noqa: E402,F401  (registers every table on Base.metadata)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def migrated_schema():
    """Build the schema exactly like production: alembic upgrade head."""
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    command.upgrade(alembic_config(), "head")
    yield
    engine.dispose()


def _truncate_all(conn) -> None:
    tables = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture(scope="module")
def db():
    """One session per test module, starting from empty tables."""
    with engine.begin() as conn:
        _truncate_all(conn)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module")
def client(db):
    from fastapi.testclient import TestClient

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def reset_rate_limiters():
    """Limiter state is process-global; isolate tests from each other."""
    from app.utils import rate_limiter

    for name in dir(rate_limiter):
        obj = getattr(rate_limiter, name)
        if isinstance(obj, rate_limiter.SimpleRateLimiter):
            obj.requests.clear()
    yield


def make_user(db, roles, username=None, password="correct-horse-battery"):
    username = username or f"user_{uuid.uuid4().hex[:8]}"
    user = User(username=username, hashed_password=hash_password(password), roles=roles)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_headers(user) -> dict:
    token = create_access_token(
        {"sub": user.username, "user_id": user.id, "roles": user.roles}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(db):
    return auth_headers(make_user(db, ["ADMIN"]))


@pytest.fixture
def trustee_headers(db):
    return auth_headers(make_user(db, ["TRUSTEE"]))
