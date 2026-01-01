from sqlalchemy import Column, Integer, String, Boolean
from app.models.base import Base


class Member(Base):
    __tablename__ = "temple_members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(50), nullable=False)
    email = Column(String(200), nullable=True)
    role = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
