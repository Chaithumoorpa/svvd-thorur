from sqlalchemy import Column, DateTime, Integer, String

from app.models.base import Base


class EmailOtp(Base):
    """One-time email verification code, gating public online seva booking on a
    real, reachable email address without requiring a full account/login.
    Only the SHA-256 hash of the code is stored."""

    __tablename__ = "email_otps"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    purpose = Column(String(50), nullable=False)
    code_hash = Column(String(64), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, nullable=False, default=0)
    used_at = Column(DateTime, nullable=True)
