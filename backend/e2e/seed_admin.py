"""Seeds one SUPER_ADMIN user for the Playwright E2E suite (frontend/e2e/).
No email on file deliberately - login is single-factor (see AuthService/
auth.py), so the UI test doesn't need to intercept a real email.

Run from backend/ with the same env vars the backend itself will use
(DATABASE_URL, SECRET_KEY, ...) plus:
  E2E_ADMIN_USERNAME (default: e2eadmin)
  E2E_ADMIN_PASSWORD (default: E2ePassword123)

    PYTHONPATH=. python e2e/seed_admin.py
"""
import os

from sqlalchemy.orm import sessionmaker

from app.core.database import engine
from app.core.security import hash_password
from app.models.user import User

USERNAME = os.environ.get("E2E_ADMIN_USERNAME", "e2eadmin")
PASSWORD = os.environ.get("E2E_ADMIN_PASSWORD", "E2ePassword123")

db = sessionmaker(bind=engine)()

existing = db.query(User).filter(User.username == USERNAME).first()
if existing:
    print(f"'{USERNAME}' already seeded")
else:
    db.add(User(
        username=USERNAME,
        hashed_password=hash_password(PASSWORD),
        roles=["SUPER_ADMIN"],
        is_active=True,
        must_change_password=False,
    ))
    db.commit()
    print(f"seeded '{USERNAME}'")
