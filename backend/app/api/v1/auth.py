import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.pagination import PageParams, page_params, paginate, set_total
from app.core.rbac import Permission, permissions_for
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import (
    PasswordChange, PublicRegister, TokenOut, UserCreate, UserLogin, UserOut, UserUpdate,
)
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.utils.dependencies import AuditContext, get_audit, get_current_user, get_db, require_permission
from app.utils.rate_limiter import get_client_ip, login_limiter, register_limiter

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger(__name__)


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


@router.post("/login", response_model=TokenOut)
def login(
    payload: UserLogin,
    request: Request,
    service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
):
    """Login with username and password. Rate limited per client IP."""
    if not login_limiter.is_allowed(get_client_ip(request)):
        raise HTTPException(status_code=429, detail="Too many login attempts. Please try again in a minute.")

    user = service.authenticate_user(payload)
    AuditService(db).record(user, "LOGIN", "user", user.id, f"{user.username} signed in", request=request)
    return {
        "access_token": service.create_access_token(user),
        "token_type": "bearer",
        "must_change_password": user.must_change_password,
    }


@router.post("/register", response_model=UserOut, status_code=201)
def register(
    payload: PublicRegister,
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    """Public self-registration. Always creates a GENERAL_USER (no admin access)."""
    if not settings.ALLOW_PUBLIC_REGISTRATION:
        raise HTTPException(status_code=403, detail="Registration is disabled")
    if not register_limiter.is_allowed(get_client_ip(request)):
        raise HTTPException(status_code=429, detail="Too many registration attempts. Please try again in a minute.")
    return service.create_general_user(payload)


@router.get("/verify", response_model=dict)
def verify_token(current_user: User = Depends(get_current_user)):
    """Current user + effective permissions. The frontend uses this to decide what UI to show."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "roles": current_user.roles,
        "permissions": sorted(p.value for p in permissions_for(current_user.roles)),
        "is_admin": current_user.is_admin,
        "is_super_admin": current_user.is_super_admin,
        "is_trustee": current_user.is_trustee,
        "must_change_password": current_user.must_change_password,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
    }


@router.post("/change-password", response_model=dict)
def change_password(
    payload: PasswordChange,
    request: Request,
    service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service.change_password(current_user, payload)
    AuditService(db).record(current_user, "PASSWORD_CHANGE", "user", current_user.id,
                            f"{current_user.username} changed their password", request=request)
    return {"message": "Password changed successfully"}


# ------------------------------------------------------------------ user management
@router.get("/admin/users", response_model=List[UserOut])
def list_users_admin(
    response: Response,
    service: AuthService = Depends(get_auth_service),
    params: PageParams = Depends(page_params),
    _: User = Depends(require_permission(Permission.USERS_MANAGE)),
):
    users, total = paginate(service.query_users(), params)
    set_total(response, total)
    return users


@router.post("/admin/users", response_model=UserOut, status_code=201)
def create_user_admin(
    payload: UserCreate,
    service: AuthService = Depends(get_auth_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(require_permission(Permission.USERS_MANAGE)),
):
    user = service.create_admin_user(payload)
    audit.log("CREATE", "user", user.id, f"Created user {user.username}", {"roles": user.roles})
    return user


@router.patch("/admin/users/{user_id}", response_model=UserOut)
def update_user_admin(
    user_id: int,
    payload: UserUpdate,
    service: AuthService = Depends(get_auth_service),
    audit: AuditContext = Depends(get_audit),
    acting_user: User = Depends(require_permission(Permission.USERS_MANAGE)),
):
    user = service.update_user(user_id, payload, acting_user)
    audit.log("UPDATE", "user", user.id, f"Updated user {user.username}", payload.model_dump(exclude_unset=True))
    return user
