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
    DeleteAccountConfirm, PasswordChange, PasswordResetConfirm, PasswordResetRequest, PublicRegister,
    TokenOut, UserCreate, UserLogin, UserOut, UserUpdate,
)
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.utils.dependencies import AuditContext, get_audit, get_current_user, get_db, require_permission
from app.utils.rate_limiter import enforce, get_client_ip, login_limiter, password_reset_limiter, register_limiter

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


@router.post("/forgot-password", response_model=dict)
def forgot_password(
    payload: PasswordResetRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    """Always returns the same generic message, whether or not the email exists,
    so the response itself never reveals which accounts are registered."""
    enforce(password_reset_limiter, get_client_ip(request), "Too many reset requests. Please try again later.")
    result = service.request_password_reset(payload.email)
    if result:
        user, raw_token = result
        link = f"{settings.FRONTEND_BASE_URL}/reset-password?token={raw_token}"
        EmailService().send(
            user.email,
            "Reset your SVVD Thorur password",
            f"Hello {user.username},\n\n"
            "We received a request to reset your SVVD Thorur admin portal password.\n\n"
            f"Reset it here (valid for 1 hour): {link}\n\n"
            "If you didn't request this, you can safely ignore this email - your password "
            "will not change.\n\n"
            "Thank you,\nSVVD Thorur",
        )
    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password", response_model=dict)
def reset_password(
    payload: PasswordResetConfirm,
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    enforce(password_reset_limiter, get_client_ip(request), "Too many attempts. Please try again later.")
    service.reset_password(payload.token, payload.new_password)
    return {"message": "Password reset successfully. You can now sign in."}


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


@router.post("/refresh", response_model=dict)
def refresh_token(
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    """Issues a fresh access token for the same session, extending it another
    ACCESS_TOKEN_EXPIRE_MINUTES from now. Requires the CURRENT token to still be
    valid - an already-expired or revoked session cannot refresh itself. Called
    silently by the frontend while the user is active (see lib/api.ts); an idle
    session simply stops being refreshed and expires on schedule."""
    return {"access_token": service.create_access_token(current_user)}


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


@router.delete("/me", response_model=dict)
def delete_my_account(
    payload: DeleteAccountConfirm,
    request: Request,
    service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Self-service account deletion (DPDPA right to erasure). The row is gone
    once delete_own_account returns, so username/email/id are captured first -
    the audit entry is written with actor=None + actor_username, the same way
    the audit trail already survives any other user's deletion."""
    user_id, username, email = current_user.id, current_user.username, current_user.email
    service.delete_own_account(current_user, payload.password)
    AuditService(db).record(None, "DELETE_ACCOUNT", "user", user_id,
                            f"{username} deleted their own account", request=request, actor_username=username)
    if email:
        EmailService().send(
            email,
            "Your SVVD Thorur account has been deleted",
            f"Hello {username},\n\n"
            "Your devotee account and its registration details have been permanently deleted, "
            "as you requested.\n\n"
            "Any sevas you already booked remain valid and on record at the temple - only the "
            "link between them and this account has been removed.\n\n"
            "If you didn't request this, please contact the temple office immediately.\n\n"
            "Thank you,\nSVVD Thorur",
        )
    return {"message": "Account deleted"}


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
    if user.email:
        link = f"{settings.FRONTEND_BASE_URL}/reset-password?token={service.issue_reset_token_for_user(user)}"
        EmailService().send(
            user.email,
            "Your SVVD Thorur account has been created",
            f"Hello {user.username},\n\n"
            "An account has been created for you on the SVVD Thorur admin portal.\n\n"
            f"Username: {user.username}\n\n"
            f"Set your password here (valid for 1 hour): {link}\n\n"
            f"If the link expires, use \"Forgot password?\" at {settings.FRONTEND_BASE_URL}/login\n\n"
            "If you weren't expecting this account, please contact the temple office.\n\n"
            "Thank you,\nSVVD Thorur",
        )
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
    if payload.password and user.email:
        link = f"{settings.FRONTEND_BASE_URL}/reset-password?token={service.issue_reset_token_for_user(user)}"
        EmailService().send(
            user.email,
            "Your SVVD Thorur password was reset",
            f"Hello {user.username},\n\n"
            "An administrator has reset your password on the SVVD Thorur admin portal.\n\n"
            f"Set your new password here (valid for 1 hour): {link}\n\n"
            f"If the link expires, use \"Forgot password?\" at {settings.FRONTEND_BASE_URL}/login\n\n"
            "If you weren't expecting this, please contact the temple office immediately.\n\n"
            "Thank you,\nSVVD Thorur",
        )
    return user
