"""Official letters and certificates on the temple letterhead.

A letter is drafted by an admin, then each chosen signatory signs it from
their OWN login (their stored signature is placed only at that moment), or is
marked as signing the printed copy in ink. Once everyone has signed, an admin
issues it: it gets a reference number (SVVD/2026/0001), the temple seal, and a
QR code that opens a public page confirming the letter is genuine - or that it
was revoked.

Signature and seal images are kept in the database (a few tens of KB each,
cleaned to a transparent PNG) rather than in the public bucket. Replacing one
retires the old row instead of deleting it, so an issued letter keeps the
exact signature it was signed with.
"""
import enum

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Enum, ForeignKey, Integer, LargeBinary, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.models.base import Base


class LetterKind(str, enum.Enum):
    GENERAL = "GENERAL"
    APPOINTMENT = "APPOINTMENT"
    MEMBERSHIP_CERTIFICATE = "MEMBERSHIP_CERTIFICATE"
    SERVICE_CERTIFICATE = "SERVICE_CERTIFICATE"
    TO_WHOM_IT_MAY_CONCERN = "TO_WHOM_IT_MAY_CONCERN"
    DONATION_ACKNOWLEDGEMENT = "DONATION_ACKNOWLEDGEMENT"
    NOC = "NOC"
    INVITATION = "INVITATION"
    # authority documents (payment gateway / bank KYC, government offices)
    POWER_OF_ATTORNEY = "POWER_OF_ATTORNEY"
    RESOLUTION = "RESOLUTION"
    AUTHORISATION = "AUTHORISATION"


class LetterStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    AWAITING_SIGNATURES = "AWAITING_SIGNATURES"
    ISSUED = "ISSUED"
    REVOKED = "REVOKED"


class SignatoryRole(str, enum.Enum):
    SIGNATORY = "SIGNATORY"  # signs the letter
    ATTESTOR = "ATTESTOR"    # attests it ("Attested by")


class SignatoryStatus(str, enum.Enum):
    PENDING = "PENDING"
    SIGNED = "SIGNED"        # signed from their own login - signature image placed
    PAPER = "PAPER"          # will sign the printed copy in ink - no image placed
    DECLINED = "DECLINED"


class LetterImageKind(str, enum.Enum):
    SIGNATURE = "SIGNATURE"
    SEAL = "SEAL"


class LetterImage(Base):
    __tablename__ = "letter_images"

    id = Column(Integer, primary_key=True)
    kind = Column(Enum(LetterImageKind), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("temple_members.id", ondelete="SET NULL"), nullable=True, index=True)
    data = Column(LargeBinary, nullable=False)  # cleaned, transparent PNG
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    retired_at = Column(DateTime, nullable=True)  # replaced or removed; kept for letters already signed with it


class OfficialLetter(Base):
    __tablename__ = "official_letters"

    id = Column(Integer, primary_key=True)
    reference_number = Column(String(30), nullable=True, unique=True)  # assigned when issued
    verify_token = Column(String(40), nullable=False, unique=True, index=True)
    kind = Column(Enum(LetterKind), nullable=False)
    status = Column(Enum(LetterStatus), nullable=False, default=LetterStatus.DRAFT, index=True)

    letter_date = Column(Date, nullable=False)
    subject = Column(String(200), nullable=False)
    recipient_name = Column(String(200), nullable=True)
    recipient_address = Column(Text, nullable=True)
    salutation = Column(String(100), nullable=True)
    body = Column(Text, nullable=False)
    closing = Column(String(100), nullable=True)
    include_seal = Column(Boolean, nullable=False, default=True, server_default="true")
    seal_image_id = Column(Integer, ForeignKey("letter_images.id", ondelete="SET NULL"), nullable=True)

    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    sent_at = Column(DateTime, nullable=True)
    issued_at = Column(DateTime, nullable=True)
    issued_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    revoke_reason = Column(String(500), nullable=True)

    signatories = relationship("LetterSignatory", back_populates="letter", cascade="all, delete-orphan",
                               order_by="LetterSignatory.sort_order")
    seal_image = relationship("LetterImage", foreign_keys=[seal_image_id])
    creator = relationship("User", foreign_keys=[created_by])


class LetterSignatory(Base):
    __tablename__ = "letter_signatories"
    __table_args__ = (UniqueConstraint("letter_id", "member_id", name="uq_letter_signatory_member"),)

    id = Column(Integer, primary_key=True)
    letter_id = Column(Integer, ForeignKey("official_letters.id", ondelete="CASCADE"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("temple_members.id", ondelete="SET NULL"), nullable=True, index=True)
    # Name and designation as printed - copied when added, so the letter does
    # not change if the member record is edited or deleted later.
    name = Column(String(200), nullable=False)
    designation = Column(String(100), nullable=True)
    role = Column(Enum(SignatoryRole), nullable=False, default=SignatoryRole.SIGNATORY)
    sort_order = Column(Integer, nullable=False, default=0)

    status = Column(Enum(SignatoryStatus), nullable=False, default=SignatoryStatus.PENDING)
    signed_at = Column(DateTime, nullable=True)
    signed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    signed_ip = Column(String(64), nullable=True)
    signature_image_id = Column(Integer, ForeignKey("letter_images.id", ondelete="SET NULL"), nullable=True)
    decline_reason = Column(String(500), nullable=True)
    marked_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # who marked PAPER

    letter = relationship("OfficialLetter", back_populates="signatories")
    member = relationship("Member")
    signature_image = relationship("LetterImage", foreign_keys=[signature_image_id])
