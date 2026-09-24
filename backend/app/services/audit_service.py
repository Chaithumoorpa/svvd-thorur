import logging
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User
from app.utils.rate_limiter import get_client_ip

logger = logging.getLogger(__name__)

# Never written to the audit trail, whatever the caller passes.
_REDACTED_KEYS = {"password", "new_password", "current_password", "hashed_password", "token", "qr_token"}

# Any deletion, hard or soft (tickets, announcements, festivals, a devotee's own
# account, ...) is logged under one of these - see the alert this triggers below.
_DELETE_ACTIONS = {"DELETE", "DELETE_ACCOUNT"}
_REPEAT_DELETE_THRESHOLD = 3
_REPEAT_DELETE_WINDOW = timedelta(minutes=10)


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: ("***" if k in _REDACTED_KEYS else _jsonable(v)) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return value


class AuditService:
    """Append-only audit trail. A failure to audit is logged but never breaks the request."""

    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        actor: Optional[User],
        action: str,
        entity_type: str,
        entity_id: Any = None,
        summary: Optional[str] = None,
        changes: Optional[dict] = None,
        request: Optional[Request] = None,
        actor_username: Optional[str] = None,
    ) -> None:
        try:
            entry = AuditLog(
                actor_id=actor.id if actor else None,
                actor_username=(actor.username if actor else actor_username),
                action=action,
                entity_type=entity_type,
                entity_id=str(entity_id) if entity_id is not None else None,
                summary=(summary or "")[:500] or None,
                changes=_jsonable(changes) if changes else None,
                ip_address=get_client_ip(request) if request is not None else None,
            )
            self.db.add(entry)
            self.db.commit()
        except Exception:  # noqa: BLE001 - auditing must not take the site down
            self.db.rollback()
            logger.exception("Failed to write audit log (%s %s %s)", action, entity_type, entity_id)
            return

        if action in _DELETE_ACTIONS and entry.actor_id is not None:
            self._maybe_alert_on_repeated_deletions(entry.actor_id)

    def _maybe_alert_on_repeated_deletions(self, actor_id: int) -> None:
        """A single account performing several deletions in a short window is
        unusual enough to be worth a Super Admin's attention - a compromised
        account, a mistake, or someone cleaning house without saying so. Fires
        once per burst (exactly when the count crosses the threshold), not on
        every deletion past it, so it doesn't spam."""
        try:
            since = datetime.utcnow() - _REPEAT_DELETE_WINDOW
            recent_count = self.db.query(AuditLog).filter(
                AuditLog.actor_id == actor_id,
                AuditLog.action.in_(_DELETE_ACTIONS),
                AuditLog.created_at >= since,
            ).count()
            if recent_count != _REPEAT_DELETE_THRESHOLD:
                return

            actor = self.db.query(User).filter(User.id == actor_id).first()
            actor_label = actor.username if actor else f"user #{actor_id}"
            super_admins = [
                u for u in self.db.query(User).filter(User.is_active.is_(True)).all()
                if u.is_super_admin and u.email
            ]
            if not super_admins:
                return

            from app.services.email_service import EmailService
            email_service = EmailService()
            for admin in super_admins:
                email_service.send(
                    admin.email,
                    "Repeated deletions on SVVD Thorur",
                    f"Hello {admin.username},\n\n"
                    f"{actor_label} has performed {recent_count} deletions in the last "
                    f"{int(_REPEAT_DELETE_WINDOW.total_seconds() // 60)} minutes.\n\n"
                    "If this is expected (a cleanup, a bulk correction), no action is needed. "
                    "If it isn't, review Admin -> Audit Log for what was deleted and by whom.\n\n"
                    "Thank you,\nSVVD Thorur",
                )
        except Exception:  # noqa: BLE001 - the alert itself must never break the request
            logger.exception("Failed to check/send repeated-deletion alert for actor_id=%s", actor_id)

    def list_page(self, params, entity_type: Optional[str] = None, action: Optional[str] = None,
                  actor: Optional[str] = None):
        from app.core.pagination import paginate

        query = self.db.query(AuditLog)
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if action:
            query = query.filter(AuditLog.action == action)
        if actor:
            query = query.filter(AuditLog.actor_username == actor)
        query = query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        return paginate(query, params)

    def recent(self, limit: int = 8):
        return (
            self.db.query(AuditLog)
            .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
            .limit(limit)
            .all()
        )
