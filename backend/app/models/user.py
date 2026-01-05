from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app.models.base import Base


class User(Base):
    """
    User = Identity (someone who can log in).
    Separate from Member/Donor which are Entities.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    phone = Column(String(20), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    roles = Column(ARRAY(String), nullable=False, default=["GENERAL_USER"])
    last_login = Column(DateTime, nullable=True)
    must_change_password = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    member = relationship("Member", back_populates="user", uselist=False)
    announcements = relationship("Announcement", back_populates="created_by")
    
    @property
    def is_super_admin(self) -> bool:
        return "SUPER_ADMIN" in (self.roles or [])
    
    @property
    def is_admin(self) -> bool:
        return any(role in ["ADMIN", "SUPER_ADMIN"] for role in (self.roles or []))
    
    @property
    def is_trustee(self) -> bool:
        return "TRUSTEE" in (self.roles or [])

    @property
    def is_staff(self) -> bool:
        return "STAFF" in (self.roles or [])
