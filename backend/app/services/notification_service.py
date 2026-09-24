import logging

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


def notify_devotees(db: Session, subject: str, body: str) -> None:
    """Best-effort email to every devotee account (an active user with an
    email on file who isn't staff, a trustee, or an admin) - used when
    something devotee-facing changes (darshan timings, a new announcement).
    Never raises: a mail hiccup must not block the change that triggered it."""
    try:
        devotees = [
            u for u in db.query(User).filter(User.is_active.is_(True), User.email.isnot(None)).all()
            if not (u.is_admin or u.is_trustee or u.is_staff)
        ]
        if not devotees:
            return
        email_service = EmailService()
        for devotee in devotees:
            email_service.send(devotee.email, subject, body)
    except Exception:  # noqa: BLE001 - notifying devotees must never break the request
        logger.exception("Failed to notify devotees: %s", subject)
