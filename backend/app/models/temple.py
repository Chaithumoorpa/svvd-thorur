from sqlalchemy import Column, Integer, String, Text, Boolean
from app.models.base import Base


class Temple(Base):
    """
    Temple profile (single active row). Everything shown on the public site
    about the temple itself lives here, not in the frontend code.
    """
    __tablename__ = "temples"

    id = Column(Integer, primary_key=True, index=True)

    # Basic identity
    name = Column(String(150), nullable=False)
    deity_name = Column(String(100), nullable=True)
    tagline = Column(String(200), nullable=True)

    # Description / history
    history = Column(Text, nullable=True)

    # Location details
    address = Column(String(300), nullable=True)
    village = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)
    map_url = Column(String(500), nullable=True)

    # Contact info (public)
    contact_phone = Column(String(20), nullable=True)
    contact_email = Column(String(100), nullable=True)
    whatsapp_number = Column(String(20), nullable=True)

    # Media / social
    hero_image_url = Column(String(500), nullable=True)
    facebook_url = Column(String(300), nullable=True)
    instagram_url = Column(String(300), nullable=True)
    youtube_url = Column(String(300), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
