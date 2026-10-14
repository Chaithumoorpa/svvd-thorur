from datetime import date, datetime
from typing import Annotated, List, Optional

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.models.letter import LetterKind, LetterStatus, SignatoryRole, SignatoryStatus
from app.schemas.common import blank_to_none

Line = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=200)]
Reason = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=500)]


def printable(v: Optional[str]) -> Optional[str]:
    """The PDF is set in a Latin font: text outside it would print as empty boxes."""
    if v is None:
        return v
    try:
        v.encode("cp1252")
    except UnicodeEncodeError:
        bad = next(ch for ch in v if not _encodes(ch))
        hint = " - write 'Rs.' instead" if bad == "₹" else ""
        raise ValueError(f"Letters print in English script for now; '{bad}' can't be printed{hint}")
    return v


def _encodes(ch: str) -> bool:
    try:
        ch.encode("cp1252")
        return True
    except UnicodeEncodeError:
        return False


class SignatoryIn(BaseModel):
    member_id: int
    role: SignatoryRole = SignatoryRole.SIGNATORY
    designation: Optional[str] = Field(default=None, max_length=100)  # defaults to the member's position

    @field_validator("designation", mode="before")
    @classmethod
    def _blank(cls, v):
        return printable(blank_to_none(v))


class LetterIn(BaseModel):
    kind: LetterKind
    letter_date: date
    subject: Line
    recipient_name: Optional[str] = Field(default=None, max_length=200)
    recipient_address: Optional[str] = Field(default=None, max_length=600)
    salutation: Optional[str] = Field(default=None, max_length=100)
    body: Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=8000)]
    closing: Optional[str] = Field(default=None, max_length=100)
    include_seal: bool = True
    signatories: List[SignatoryIn] = Field(default_factory=list, max_length=6)

    @field_validator("recipient_name", "recipient_address", "salutation", "closing", mode="before")
    @classmethod
    def _blank(cls, v):
        return blank_to_none(v.strip() if isinstance(v, str) else v)

    @field_validator("subject", "recipient_name", "recipient_address", "salutation", "body", "closing")
    @classmethod
    def _printable(cls, v):
        return printable(v)

    @field_validator("signatories")
    @classmethod
    def _unique(cls, v):
        ids = [s.member_id for s in v]
        if len(ids) != len(set(ids)):
            raise ValueError("A member can be added only once")
        return v


class SignIn(BaseModel):
    password: str = Field(min_length=1, max_length=200)


class ReasonIn(BaseModel):
    reason: Reason


class ImageIn(BaseModel):
    image: str = Field(min_length=20, max_length=9_000_000)  # data URL; size re-checked after decoding


# ---- output -------------------------------------------------------------------------------
class SignatoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    member_id: Optional[int] = None
    name: str
    designation: Optional[str] = None
    role: SignatoryRole
    status: SignatoryStatus
    signed_at: Optional[datetime] = None
    decline_reason: Optional[str] = None
    has_login: bool = False
    has_signature: bool = False


class LetterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reference_number: Optional[str] = None
    kind: LetterKind
    status: LetterStatus
    letter_date: date
    subject: str
    recipient_name: Optional[str] = None
    recipient_address: Optional[str] = None
    salutation: Optional[str] = None
    body: str
    closing: Optional[str] = None
    include_seal: bool
    created_at: datetime
    created_by_name: Optional[str] = None
    sent_at: Optional[datetime] = None
    issued_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    revoke_reason: Optional[str] = None
    verify_url: Optional[str] = None
    signatories: List[SignatoryOut] = []


class LetterTemplate(BaseModel):
    kind: LetterKind
    label: str
    certificate_title: Optional[str] = None
    subject: str
    salutation: str
    body: str
    closing: str


class SignatureStatus(BaseModel):
    member_id: int
    name: str
    position: Optional[str] = None
    is_active: bool
    has_login: bool
    has_signature: bool
    uploaded_at: Optional[datetime] = None


class SealStatus(BaseModel):
    has_seal: bool
    uploaded_at: Optional[datetime] = None


class PendingSignature(BaseModel):
    letter_id: int
    signatory_id: int
    role: SignatoryRole
    subject: str
    kind: LetterKind
    letter_date: date
    recipient_name: Optional[str] = None
    sent_at: Optional[datetime] = None
    requested_by: Optional[str] = None


class MySignature(BaseModel):
    member_id: Optional[int] = None    # None: this login isn't linked to a committee member
    member_name: Optional[str] = None
    has_signature: bool = False
    uploaded_at: Optional[datetime] = None
    pending: List[PendingSignature] = []


class VerifiedSignatory(BaseModel):
    name: str
    designation: Optional[str] = None
    role: SignatoryRole
    method: str                         # "digital" | "ink"
    signed_at: Optional[datetime] = None


class LetterVerification(BaseModel):
    reference_number: str
    status: LetterStatus                # ISSUED or REVOKED
    kind_label: str
    subject: str
    recipient_name: Optional[str] = None
    letter_date: date
    issued_at: datetime
    revoked_at: Optional[datetime] = None
    revoke_reason: Optional[str] = None
    temple_name: str
    signatories: List[VerifiedSignatory]
