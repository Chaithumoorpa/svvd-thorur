import re
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.common import normalize_mobile


class UserRole(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    TRUSTEE = "TRUSTEE"
    STAFF = "STAFF"
    GENERAL_USER = "GENERAL_USER"


_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.@-]{3,100}$")


def _validate_password(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if len(value) > 128:
        raise ValueError("Password is too long")
    if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
        raise ValueError("Password must contain at least one letter and one digit")
    return value


class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=20)
    is_active: Optional[bool] = True
    roles: List[UserRole] = [UserRole.GENERAL_USER]

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if not _USERNAME_RE.match(v):
            raise ValueError("Username must be 3-100 characters: letters, digits, . _ @ -")
        return v

    @field_validator("roles")
    @classmethod
    def validate_roles(cls, v):
        if not v:
            raise ValueError("User must have at least one role")
        # de-duplicate while keeping a stable order
        return sorted(set(v), key=lambda r: r.value)


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password(v)


class PublicRegister(BaseModel):
    """Self-registration: can never choose roles. Email and phone are required -
    a devotee account is only useful if the temple can reach its owner, and a
    booking's contact details already require both anyway."""
    username: str
    email: EmailStr
    phone: str = Field(max_length=20)
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if not _USERNAME_RE.match(v):
            raise ValueError("Username must be 3-100 characters: letters, digits, . _ @ -")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return normalize_mobile(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password(v)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=20)
    is_active: Optional[bool] = None
    roles: Optional[List[UserRole]] = None
    password: Optional[str] = None  # admin-initiated reset; forces a change at next login

    @field_validator("roles")
    @classmethod
    def validate_roles(cls, v):
        if v is not None and not v:
            raise ValueError("User must have at least one role")
        return sorted(set(v), key=lambda r: r.value) if v else v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        return _validate_password(v) if v is not None else v


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    roles: List[str]
    must_change_password: bool
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenOut(Token):
    must_change_password: bool


class PasswordChange(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return _validate_password(v)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return _validate_password(v)
