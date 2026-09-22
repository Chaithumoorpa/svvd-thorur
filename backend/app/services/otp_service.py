import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import create_access_token, decode_access_token
from app.models.email_otp import EmailOtp
from app.services.email_service import EmailService

OTP_TTL = timedelta(minutes=10)
MAX_ATTEMPTS = 5
BOOKING_TOKEN_TTL = timedelta(minutes=30)
BOOKING_PURPOSE = "seva_booking"


class OtpService:
    """Email one-time-code verification, gating public online seva booking on a
    real, reachable email address without a full account/login. On success,
    issues a short-lived signed token (not a DB row) proving that email was
    verified, which the booking endpoint requires and checks against the
    email in the booking payload."""

    def __init__(self, db: Session):
        self.db = db

    def request_otp(self, email: str) -> str:
        """Emails the code and returns it too - the raw code is never included in
        any API response; callers (see the router) discard the return value and
        it exists only so tests can drive the verify step without reading email.

        Unlike most of this codebase's email sends (best-effort, silent on
        failure - a mail hiccup shouldn't block the action that triggered it),
        a devotee stuck on the OTP step with no code coming needs to know
        immediately rather than wait forever for an email that was never
        actually accepted by SES - there's no account-enumeration concern here
        to justify staying silent, unlike forgot-password."""
        email = email.strip().lower()
        code = f"{secrets.randbelow(1_000_000):06d}"
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        self.db.add(EmailOtp(
            email=email, purpose=BOOKING_PURPOSE, code_hash=code_hash, expires_at=now + OTP_TTL,
        ))
        self.db.commit()
        sent = EmailService().send(
            email,
            "Your SVVD Thorur verification code",
            f"Your verification code is: {code}\n\n"
            "It is valid for 10 minutes - enter it on the booking page to continue.\n\n"
            "If you didn't request this, you can safely ignore this email.\n\n"
            "Thank you,\nSVVD Thorur",
        )
        if not sent:
            raise HTTPException(
                status_code=502,
                detail="Could not send the verification email. Please check the address and try again.",
            )
        return code

    def verify_otp(self, email: str, code: str) -> str:
        email = email.strip().lower()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        record = (
            self.db.query(EmailOtp)
            .filter(
                EmailOtp.email == email, EmailOtp.purpose == BOOKING_PURPOSE,
                EmailOtp.used_at.is_(None), EmailOtp.expires_at >= now,
            )
            .order_by(EmailOtp.id.desc())
            .first()
        )
        if not record or record.attempts >= MAX_ATTEMPTS:
            raise HTTPException(
                status_code=400, detail="No active code for this email. Please request a new one.",
            )

        if not secrets.compare_digest(hashlib.sha256(code.encode()).hexdigest(), record.code_hash):
            record.attempts += 1
            self.db.commit()
            raise HTTPException(status_code=400, detail="Incorrect code. Please try again.")

        record.used_at = now
        self.db.commit()
        return create_access_token({"purpose": BOOKING_PURPOSE, "email": email}, expires_delta=BOOKING_TOKEN_TTL)

    @staticmethod
    def check_booking_token(token: str, email: str) -> None:
        payload = decode_access_token(token)
        if not payload or payload.get("purpose") != BOOKING_PURPOSE \
                or payload.get("email") != email.strip().lower():
            raise HTTPException(status_code=400, detail="Please verify your email again")
