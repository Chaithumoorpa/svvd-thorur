import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from fastapi import HTTPException

from app.core.security import create_access_token, hash_password, verify_password
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import PasswordChange, PublicRegister, UserCreate, UserLogin, UserUpdate

# How long an emailed password-reset link stays valid.
RESET_TOKEN_TTL = timedelta(hours=1)

# Verified when the username does not exist so both failure paths cost the same time
# (prevents user enumeration through response timing).
_DUMMY_HASH = hash_password("timing-equalisation-only")


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.logger = logging.getLogger(__name__)

    # ---- login -----------------------------------------------------------------
    def authenticate_user(self, data: UserLogin) -> User:
        user = self.user_repository.get_by_username(data.username.strip())
        password_ok = verify_password(data.password, user.hashed_password if user else _DUMMY_HASH)
        if not user or not password_ok or not user.is_active:
            self.logger.warning("Authentication failed for username: %s", data.username)
            raise HTTPException(status_code=401, detail="Invalid username or password")

        user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)
        self.user_repository.update(user)
        return user

    def create_access_token(self, user: User) -> str:
        # Roles are informational only; the API always re-reads them from the database.
        return create_access_token({"sub": user.username, "user_id": user.id})

    # ---- user creation -----------------------------------------------------------
    def _ensure_unique(self, username: Optional[str], email: Optional[str], exclude_id: Optional[int] = None):
        if username:
            existing = self.user_repository.get_by_username(username)
            if existing and existing.id != exclude_id:
                raise HTTPException(status_code=400, detail="Username already exists")
        if email:
            existing = self.user_repository.get_by_email(email)
            if existing and existing.id != exclude_id:
                raise HTTPException(status_code=400, detail="Email already in use")

    def create_admin_user(self, data: UserCreate) -> User:
        """Create a user with explicit roles (SUPER_ADMIN only at the API layer)."""
        self._ensure_unique(data.username, data.email)
        user = User(
            username=data.username,
            email=data.email,
            phone=data.phone,
            hashed_password=hash_password(data.password),
            roles=[role.value for role in data.roles],
            is_active=True if data.is_active is None else data.is_active,
            must_change_password=True,
        )
        return self.user_repository.create(user)

    def create_general_user(self, data: PublicRegister) -> User:
        """Public self-registration: always GENERAL_USER, no admin access."""
        self._ensure_unique(data.username, data.email)
        user = User(
            username=data.username,
            email=data.email,
            phone=data.phone,
            hashed_password=hash_password(data.password),
            roles=["GENERAL_USER"],
            must_change_password=False,
        )
        return self.user_repository.create(user)

    # ---- management ----------------------------------------------------------------
    def query_users(self):
        return self.user_repository.query_all()

    def update_user(self, user_id: int, data: UserUpdate, acting_user: User) -> User:
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        fields = data.model_dump(exclude_unset=True)
        self._ensure_unique(None, fields.get("email"), exclude_id=user.id)

        new_roles = [r.value if hasattr(r, "value") else r for r in fields["roles"]] if "roles" in fields else None
        deactivating = fields.get("is_active") is False
        demoting = new_roles is not None and "SUPER_ADMIN" not in new_roles and user.is_super_admin

        if user.id == acting_user.id and (deactivating or demoting):
            raise HTTPException(status_code=400, detail="You cannot remove your own access")
        if user.is_super_admin and (deactivating or demoting) \
                and self.user_repository.count_active_super_admins() <= 1:
            raise HTTPException(status_code=400, detail="At least one active Super Admin is required")

        for key in ("email", "phone", "is_active"):
            if key in fields:
                setattr(user, key, fields[key])
        if new_roles is not None:
            user.roles = new_roles
        if fields.get("password"):
            user.hashed_password = hash_password(fields["password"])
            user.must_change_password = True
        return self.user_repository.update(user)

    def change_password(self, user: User, data: PasswordChange) -> User:
        if not verify_password(data.current_password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Incorrect current password")
        if data.current_password == data.new_password:
            raise HTTPException(status_code=400, detail="New password must differ from the current one")

        user.hashed_password = hash_password(data.new_password)
        user.must_change_password = False
        return self.user_repository.update(user)

    # ---- forgot password (email link) ------------------------------------------
    def _issue_reset_token(self, user: User) -> str:
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        db = self.user_repository.db
        db.add(PasswordResetToken(
            user_id=user.id, token_hash=token_hash, expires_at=now + RESET_TOKEN_TTL,
        ))
        db.commit()
        return raw_token

    def issue_reset_token_for_user(self, user: User) -> str:
        """Used when an admin creates a user or resets their password: the
        welcome/reset email links here instead of carrying the admin-chosen
        password in plaintext, so that string never travels over email."""
        return self._issue_reset_token(user)

    def request_password_reset(self, email: str) -> Optional[Tuple[User, str]]:
        """Issues a one-hour, single-use reset token for the account with this
        email, if any. Returns (user, raw_token) to email, or None when there's
        no active account for that address - callers must show the same
        "check your email" message either way, to avoid leaking which is true."""
        user = self.user_repository.get_by_email(email.strip())
        if not user or not user.is_active:
            # Same token-generation/hashing cost as the real path below, so response
            # time doesn't reveal whether the account exists - only the DB write is
            # actually skipped. Mirrors _DUMMY_HASH's role in authenticate_user above.
            hashlib.sha256(secrets.token_urlsafe(32).encode()).hexdigest()
            return None
        return user, self._issue_reset_token(user)

    def reset_password(self, token: str, new_password: str) -> None:
        db = self.user_repository.db
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        record = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if not record or record.used_at is not None or record.expires_at < now:
            raise HTTPException(status_code=400, detail="This reset link is invalid or has expired")

        user = self.user_repository.get_by_id(record.user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=400, detail="This reset link is invalid or has expired")

        user.hashed_password = hash_password(new_password)
        user.must_change_password = False
        record.used_at = now
        db.add(user)
        db.add(record)
        db.commit()
