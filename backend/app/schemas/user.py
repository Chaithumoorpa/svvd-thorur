from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from enum import Enum

class UserRole(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    TRUSTEE = "TRUSTEE"
    STAFF = "STAFF"
    GENERAL_USER = "GENERAL_USER"

class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = True
    roles: List[UserRole] = [UserRole.GENERAL_USER]
    
    @field_validator('roles')
    @classmethod
    def validate_roles(cls, v):
        if not v or len(v) == 0:
            raise ValueError('User must have at least one role')
        
        # Validate each role is a valid UserRole enum
        valid_roles = {role.value for role in UserRole}
        for role in v:
            role_value = role.value if hasattr(role, 'value') else str(role)
            if role_value not in valid_roles:
                raise ValueError(
                    f'Invalid role: {role_value}. Valid roles are: {", ".join(valid_roles)}'
                )
        
        # Remove duplicates
        return list(set(v))

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(UserBase):
    id: int
    must_change_password: bool
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenOut(Token):
    must_change_password: bool

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
