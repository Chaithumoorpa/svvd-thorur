from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base


class Member(Base):
    """
    Member = Entity (temple committee member / staff).
    Phone and email are PRIVATE; only name/position/photo are published, and
    only when `show_on_website` is set.
    A member MAY have a linked User account (optional).
    """
    __tablename__ = "temple_members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(50), nullable=False)
    email = Column(String(200), nullable=True)
    position = Column(String(100), nullable=True)  # e.g., Trustee, Priest, Staff
    is_active = Column(Boolean, default=True, nullable=False)

    # Public committee page
    show_on_website = Column(Boolean, default=False, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    photo_url = Column(String(500), nullable=True)

    # Optional link to User (member may or may not have login access)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, unique=True)
    user = relationship("User", back_populates="member")
