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
LOGIN_PURPOSE = "login"
REGISTER_PURPOSE = "register"
# However many IPs the requests come from, one address gets at most this many
# codes per window - so the form can't be used to flood someone's inbox (or run
# up the temple's mail sending).
MAX_CODES_PER_EMAIL = 5
CODE_WINDOW = timedelta(minutes=15)


class OtpService:
    """Email one-time-code verification. Two purposes share this table/
    logic, kept apart by `purpose` so a code for one never collides with or
    gets cross-verified against the other:
    - seva_booking: gates public online booking on a real, reachable email,
      without a full account/login (see request_otp/verify_otp).
    - login: the second factor on top of password for any account with an
      email on file (see request_login_otp/verify_login_otp) - accounts with
      no email skip this, since there'd be nowhere to send the code."""

    def __init__(self, db: Session):
        self.db = db

    def _create_code(self, email: str, purpose: str) -> str:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        recent = self.db.query(EmailOtp).filter(
            EmailOtp.email == email, EmailOtp.purpose == purpose, EmailOtp.created_at >= now - CODE_WINDOW,
        ).count()
        if recent >= MAX_CODES_PER_EMAIL:
            raise HTTPException(status_code=429, detail=(
                "Too many codes have been sent to this email address. Please wait 15 minutes and try again."))
        code = f"{secrets.randbelow(1_000_000):06d}"
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        self.db.add(EmailOtp(email=email, purpose=purpose, code_hash=code_hash, expires_at=now + OTP_TTL))
        self.db.commit()
        return code

    def _consume_code(self, email: str, purpose: str, code: str) -> None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        record = (
            self.db.query(EmailOtp)
            .filter(
                EmailOtp.email == email, EmailOtp.purpose == purpose,
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

    # ---- seva booking (public, no account required) -----------------------------------
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
        code = self._create_code(email, BOOKING_PURPOSE)
        sent = EmailService().send(
            email,
            "Your SVVD Thorur verification code",
            f"Your verification code is: {code}\n\n"
            "It is valid for 10 minutes - enter it on the booking page to continue.\n\n"
            "If you didn't request this, you can safely ignore this email.\n\n"
            "Thank you,\nSVVD Thorur",
            code=code, heading="Your verification code",
        )
        if not sent:
            raise HTTPException(
                status_code=502,
                detail="Could not send the verification email. Please check the address and try again.",
            )
        return code

    def verify_otp(self, email: str, code: str) -> str:
        email = email.strip().lower()
        self._consume_code(email, BOOKING_PURPOSE, code)
        return create_access_token(
            {"typ": "booking", "purpose": BOOKING_PURPOSE, "email": email}, expires_delta=BOOKING_TOKEN_TTL,
        )

    @staticmethod
    def check_booking_token(token: str, email: str) -> None:
        payload = decode_access_token(token)
        if not payload or payload.get("typ") != "booking" or payload.get("purpose") != BOOKING_PURPOSE \
                or payload.get("email") != email.strip().lower():
            raise HTTPException(status_code=400, detail="Please verify your email again")

    # ---- login second factor (an existing account, already past the password check) ---
    def request_login_otp(self, email: str) -> str:
        """Same shape as request_otp, but under LOGIN_PURPOSE. Called only after
        the password has already been verified correct (see /auth/login), so
        unlike request_otp there's no meaningful enumeration concern in failing
        loudly - the caller already proved they know the account's password."""
        email = email.strip().lower()
        code = self._create_code(email, LOGIN_PURPOSE)
        sent = EmailService().send(
            email,
            "Your SVVD Thorur sign-in code",
            f"Your sign-in code is: {code}\n\n"
            "It is valid for 10 minutes. If you didn't just try to sign in, your password "
            "may be compromised - change it as soon as you can.\n\n"
            "Thank you,\nSVVD Thorur",
            code=code, heading="Your sign-in code", tone="alert",
        )
        if not sent:
            raise HTTPException(
                status_code=502, detail="Could not send the sign-in code. Please try again.",
            )
        return code

    # ---- sign-up (prove the email before any account exists) --------------------------
    def request_register_otp(self, email: str) -> str:
        email = email.strip().lower()
        code = self._create_code(email, REGISTER_PURPOSE)
        sent = EmailService().send(
            email,
            "Your SVVD Thorur sign-up code",
            f"Your sign-up code is: {code}\n\n"
            "Enter it on the sign-up page to confirm this is your email address. It is valid for "
            "10 minutes.\n\n"
            "If you didn't try to create an account, you can safely ignore this email - no account "
            "has been created.\n\n"
            "Thank you,\nSVVD Thorur",
            code=code, heading="Confirm your email",
        )
        if not sent:
            raise HTTPException(
                status_code=502,
                detail="Could not send the verification email. Please check the address and try again.",
            )
        return code

    def verify_register_otp(self, email: str, code: str) -> None:
        self._consume_code(email.strip().lower(), REGISTER_PURPOSE, code)

    def verify_login_otp(self, email: str, code: str) -> None:
        self._consume_code(email.strip().lower(), LOGIN_PURPOSE, code)
