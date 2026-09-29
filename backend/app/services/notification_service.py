import logging
from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

NOTIFICATION_PREF_PURPOSE = "notification_pref"
NOTIFICATION_PREF_TOKEN_TTL = timedelta(days=400)  # outlives the email itself


def notify_devotees(db: Session, subject: str, body: str) -> None:
    """Best-effort email to every devotee account (an active user with an
    email on file who isn't staff, a trustee, or an admin, and who hasn't
    opted out) - used when something devotee-facing changes (darshan timings,
    a new announcement). Each devotee gets their own one-click unsubscribe
    link appended, since this is a broadcast they didn't ask for on a
    per-message basis. Never raises: a mail hiccup must not block the change
    that triggered it."""
    try:
        devotees = [
            u for u in db.query(User).filter(
                User.is_active.is_(True), User.email.isnot(None), User.receive_notifications.is_(True),
            ).all()
            if not (u.is_admin or u.is_trustee or u.is_staff)
        ]
        if not devotees:
            return
        email_service = EmailService()
        for devotee in devotees:
            email_service.send(devotee.email, subject, f"{body}\n\n{_unsubscribe_line(devotee)}")
    except Exception:  # noqa: BLE001 - notifying devotees must never break the request
        logger.exception("Failed to notify devotees: %s", subject)


def _unsubscribe_line(devotee: User) -> str:
    token = create_access_token(
        {"purpose": NOTIFICATION_PREF_PURPOSE, "user_id": devotee.id},
        expires_delta=NOTIFICATION_PREF_TOKEN_TTL,
    )
    return (
        "Don't want these emails? Manage your notification preferences: "
        f"{settings.FRONTEND_BASE_URL}/unsubscribe?token={token}"
    )
