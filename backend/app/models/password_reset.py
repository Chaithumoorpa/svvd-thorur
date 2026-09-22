from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.models.base import Base


class PasswordResetToken(Base):
    """A single-use, time-limited token emailed to a user who requested a
    password reset. Only the SHA-256 hash is stored - the raw token exists
    only in the emailed link and is never persisted."""

    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
