import logging
from datetime import date, datetime, time
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
