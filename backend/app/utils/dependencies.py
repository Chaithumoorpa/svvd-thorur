import logging
from typing import Callable

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db  # noqa: F401  (re-exported for routers)
from app.core.rbac import Permission, has_permission, permissions_for
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.announcement_repo import AnnouncementRepository
from app.repositories.contact_repo import ContactRepository
from app.repositories.donor_repo import DonorRepository
from app.repositories.festival_repo import FestivalRepository
from app.repositories.gallery_repo import GalleryRepository
from app.repositories.member_repo import MemberRepository
from app.repositories.pooja_repo import PoojaRepository
from app.repositories.seva_ticket_repo import SevaTicketRepository
from app.services.announcement_service import AnnouncementService
from app.services.audit_service import AuditService
from app.services.contact_service import ContactService
from app.services.donor_service import DonorService
from app.services.festival_service import FestivalService
from app.services.gallery_service import GalleryService
from app.services.member_service import MemberService
from app.services.pooja_service import PoojaService
from app.services.otp_service import OtpService
from app.services.seva_ticket_service import SevaTicketService
from app.services.storage_service import StorageService

security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- auth
def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate the JWT and load the user. Roles are ALWAYS taken from the database row,
    never from the token, so demoting/deactivating a user takes effect immediately.
    """
    if credentials is None:
        raise HTTPException(
            status_code=401, detail="Not authenticated", headers={"WWW-Authenticate": "Bearer"}
        )

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        logger.warning("Authentication failed for user_id=%s (missing or inactive)", user_id)
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User | None:
    """Like get_current_user, but a missing/invalid/expired token means "anonymous"
    instead of a 401 - for endpoints that work either way (e.g. online booking links
    the ticket to the devotee's account when they happen to be signed in)."""
    if credentials is None:
        return None
    payload = decode_access_token(credentials.credentials)
    if not payload:
        return None
    user = db.query(User).filter(User.id == payload.get("user_id")).first()
    return user if user and user.is_active else None


def require_permission(*required: Permission) -> Callable[..., User]:
    """Dependency factory: the user must hold ALL listed permissions."""

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        for permission in required:
            if not has_permission(current_user.roles, permission):
                logger.warning(
                    "Permission denied: user=%s roles=%s needs=%s",
                    current_user.username, current_user.roles, permission.value,
                )
                raise HTTPException(status_code=403, detail="You do not have permission to do this")
        return current_user

    return dependency


def require_any_permission(*options: Permission) -> Callable[..., User]:
    """Dependency factory: the user must hold AT LEAST ONE of the listed permissions."""

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        granted = permissions_for(current_user.roles)
        if not any(p in granted for p in options):
            raise HTTPException(status_code=403, detail="You do not have permission to do this")
        return current_user

    return dependency


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """ADMIN or SUPER_ADMIN."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """SUPER_ADMIN only."""
    if not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Super Admin access required")
    return current_user


def require_trustee(current_user: User = Depends(get_current_user)) -> User:
    """TRUSTEE, ADMIN or SUPER_ADMIN (read access to sensitive finance / donor data)."""
    if not (current_user.is_trustee or current_user.is_admin):
        raise HTTPException(status_code=403, detail="Trustee access required")
    return current_user


# Legacy aliases
get_current_admin_user = require_admin
get_current_trustee_user = require_trustee


# --------------------------------------------------------------------------- audit
class AuditContext:
    """Bound to one request: records an audit entry for the authenticated actor."""

    def __init__(self, db: Session, request: Request, actor: User):
        self._service = AuditService(db)
        self._request = request
        self._actor = actor

    def log(self, action: str, entity_type: str, entity_id=None, summary: str | None = None,
            changes: dict | None = None) -> None:
        self._service.record(
            self._actor, action, entity_type, entity_id, summary, changes, request=self._request
        )


def get_audit(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AuditContext:
    return AuditContext(db, request, current_user)


def get_audit_service(db: Session = Depends(get_db)) -> AuditService:
    return AuditService(db)


# --------------------------------------------------------------------------- services
def get_pooja_repository(db: Session = Depends(get_db)) -> PoojaRepository:
    return PoojaRepository(db)


def get_pooja_service(db: Session = Depends(get_db)) -> PoojaService:
    return PoojaService(PoojaRepository(db))


def get_member_repository(db: Session = Depends(get_db)) -> MemberRepository:
    return MemberRepository(db)


def get_member_service(db: Session = Depends(get_db)) -> MemberService:
    return MemberService(MemberRepository(db))


def get_donor_repository(db: Session = Depends(get_db)) -> DonorRepository:
    return DonorRepository(db)


def get_donor_service(db: Session = Depends(get_db)) -> DonorService:
    return DonorService(DonorRepository(db))


def get_gallery_repository(db: Session = Depends(get_db)) -> GalleryRepository:
    return GalleryRepository(db)


def get_gallery_service(db: Session = Depends(get_db)) -> GalleryService:
    return GalleryService(GalleryRepository(db))


def get_storage_service() -> StorageService:
    return StorageService()


def get_seva_ticket_repository(db: Session = Depends(get_db)) -> SevaTicketRepository:
    return SevaTicketRepository(db)


def get_seva_ticket_service(db: Session = Depends(get_db)) -> SevaTicketService:
    return SevaTicketService(SevaTicketRepository(db), PoojaRepository(db))


def get_otp_service(db: Session = Depends(get_db)) -> OtpService:
    return OtpService(db)


def get_announcement_repository(db: Session = Depends(get_db)) -> AnnouncementRepository:
    return AnnouncementRepository(db)


def get_announcement_service(db: Session = Depends(get_db)) -> AnnouncementService:
    return AnnouncementService(AnnouncementRepository(db))


def get_festival_repository(db: Session = Depends(get_db)) -> FestivalRepository:
    return FestivalRepository(db)


def get_festival_service(db: Session = Depends(get_db)) -> FestivalService:
    return FestivalService(FestivalRepository(db))


def get_contact_repository(db: Session = Depends(get_db)) -> ContactRepository:
    return ContactRepository(db)


def get_contact_service(db: Session = Depends(get_db)) -> ContactService:
    return ContactService(ContactRepository(db))
