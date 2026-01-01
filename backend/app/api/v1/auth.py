from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import time
import logging

from app.utils.dependencies import get_db, get_current_user, require_super_admin
from app.models.user import User
from app.utils.rate_limiter import login_limiter, register_limiter, get_client_ip
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate, UserLogin, TokenOut, PasswordChange, UserOut
from typing import List

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger(__name__)


def get_auth_service(
    db: Session = Depends(get_db),
) -> AuthService:
    repo = UserRepository(db)
    return AuthService(repo)


@router.post("/login", response_model=TokenOut)
def login(
    payload: UserLogin,
    service: AuthService = Depends(get_auth_service),
    request: Request = None,
):
    """
    Login with username and password.
    Returns JWT access token.
    Rate limited: 5 requests per minute per IP.
    """
    # Rate limiting check
    client_ip = get_client_ip(request)
    if not login_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Please try again in a minute."
        )
    
    user = service.authenticate_user(payload)
    token = service.create_access_token(user)
    
    logger.info(
        f"User logged in: username={user.username}, "
        f"roles={user.roles}, must_change_password={user.must_change_password}"
    )
    
    return {
        "access_token": token, 
        "token_type": "bearer",
        "must_change_password": user.must_change_password
    }


@router.get("/admin/users", response_model=List[UserOut])
def list_users_admin(
    service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(require_super_admin)
):
    """
    List all users. Restricted to SUPER_ADMIN.
    """
    logger.info(f"Users list requested by admin: {current_user.username}")
    return service.list_users()


@router.post("/register", response_model=UserOut)
def register(
    payload: UserCreate,
    service: AuthService = Depends(get_auth_service),
    request: Request = None
):
    """
    Register a new general user.
    Rate limited: 5 requests per minute per IP.
    """
    # Rate limiting check
    client_ip = get_client_ip(request)
    if not register_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Too many registration attempts. Please try again in a minute."
        )
    
    logger.info(f"New user registration: username={payload.username}")
    
    user = service.create_general_user(payload)
    return user


@router.post("/admin/users", response_model=UserOut)
def create_user_admin(
    payload: UserCreate,
    service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(require_super_admin)
):
    """
    Create a new user with specific roles. Restricted to SUPER_ADMIN.
    """
    logger.info(
        f"Admin user creation: by={current_user.username}, "
        f"new_username={payload.username}, roles={payload.roles}"
    )
    
    user = service.create_admin_user(payload)
    return user

@router.post("/change-password", response_model=dict)
def change_password(
    payload: PasswordChange,
    service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_user)
):
    """
    Change password for the current user.
    """
    service.change_password(current_user, payload)
    return {"message": "Password changed successfully"}


@router.get("/verify", response_model=dict)
def verify_token(
    current_user: User = Depends(get_current_user)
):
    """
    Verify current token and return user info.
    Used by frontend to check auth status.
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "roles": current_user.roles,  # Array of roles
        "is_admin": current_user.is_admin,  # True if ADMIN or SUPER_ADMIN
        "is_super_admin": current_user.is_super_admin,  # True if SUPER_ADMIN
        "is_trustee": current_user.is_trustee,  # True if TRUSTEE
        "must_change_password": current_user.must_change_password,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None
    }
