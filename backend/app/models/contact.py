from sqlalchemy import Column, Integer, String, Text, Enum, Index
import enum
from app.models.base import Base

class ContactStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"

class ContactMessage(Base):
    __tablename__ = "contact_messages"
    __table_args__ = (Index("ix_contact_messages_created_at", "created_at"),)  # the admin inbox, newest first

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(Enum(ContactStatus), default=ContactStatus.PENDING, nullable=False)
    admin_notes = Column(Text, nullable=True)
