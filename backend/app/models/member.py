from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    full_name = Column(String(200), nullable=False)
    designation = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    joining_date = Column(DateTime, nullable=True)
    address = Column(String(500), nullable=True)
    emergency_contact = Column(String(50), nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationship
    user = relationship("User", back_populates="member")
