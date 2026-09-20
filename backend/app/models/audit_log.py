from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Index
from app.models.base import Base


class AuditLog(Base):
    """Append-only record of who changed what. Never updated or deleted by the app."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_username = Column(String(100), nullable=True)  # survives user deletion
    action = Column(String(30), nullable=False)          # CREATE / UPDATE / DELETE / LOGIN ...
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(64), nullable=True)
    summary = Column(String(500), nullable=True)
    changes = Column(JSON, nullable=True)
    ip_address = Column(String(64), nullable=True)

    __table_args__ = (
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
        Index("ix_audit_logs_created_at", "created_at"),
    )
