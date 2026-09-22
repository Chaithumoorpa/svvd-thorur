import os

# Must be set before the app (and its Settings object) is imported.
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-long-enough-1234567890")
os.environ.setdefault("ENV", "development")
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("ALLOW_PUBLIC_REGISTRATION", "true")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.database import get_db  # noqa: E402
from app.core.security import create_access_token, hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models.base import Base  # noqa: E402
from app.models.user import User  # noqa: E402
from app.utils import rate_limiter  # noqa: E402


@pytest.fixture()
def db():
    """A fresh in-memory database per test."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    # limiters are process-global; reset so tests do not affect each other
    for limiter in (rate_limiter.login_limiter, rate_limiter.register_limiter,
                    rate_limiter.contact_limiter, rate_limiter.booking_limiter,
                    rate_limiter.password_reset_limiter, rate_limiter.otp_request_limiter,
                    rate_limiter.otp_verify_limiter):
        limiter.requests.clear()
    # No `with`: skips the lifespan (which validates Alembic against a real database).
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def make_user(db):
    """Create a user directly in the database and return (user, auth_headers)."""
    counter = {"n": 0}

    def _make(*roles: str, username: str | None = None, password: str = "Password123", **extra):
        counter["n"] += 1
        user = User(
            username=username or f"user{counter['n']}",
            hashed_password=hash_password(password),
            roles=list(roles) or ["GENERAL_USER"],
            **extra,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_access_token({"sub": user.username, "user_id": user.id})
        return user, {"Authorization": f"Bearer {token}"}

    return _make


@pytest.fixture()
def super_admin(make_user):
    return make_user("SUPER_ADMIN", username="root")


@pytest.fixture()
def admin(make_user):
    return make_user("ADMIN", username="admin")


@pytest.fixture()
def trustee(make_user):
    return make_user("TRUSTEE", username="trustee")


@pytest.fixture()
def staff(make_user):
    return make_user("STAFF", username="staff")


@pytest.fixture()
def visitor(make_user):
    return make_user("GENERAL_USER", username="visitor")
