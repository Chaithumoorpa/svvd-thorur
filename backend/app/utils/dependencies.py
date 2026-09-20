from typing import Generator, Optional
import logging
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.repositories.pooja_repo import PoojaRepository
from app.services.pooja_service import PoojaService
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.repositories.member_repo import MemberRepository
from app.services.member_service import MemberService
from app.repositories.donor_repo import DonorRepository
from app.services.donor_service import DonorService
from app.repositories.gallery_repo import GalleryRepository
from app.services.gallery_service import GalleryService
from app.repositories.seva_ticket_repo import SevaTicketRepository
from app.services.seva_ticket_service import SevaTicketService
from app.repositories.announcement_repo import AnnouncementRepository
from app.services.announcement_service import AnnouncementService
from app.repositories.festival_repo import FestivalRepository
from app.services.festival_service import FestivalService
from app.repositories.contact_repo import ContactRepository
from app.services.contact_service import ContactService

security = HTTPBearer()
logger = logging.getLogger(__name__)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate JWT token and return current user.
    Raises 401 if token is invalid or expired.
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if not payload:
        logger.warning("Authentication failed: Invalid or expired token")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    user_id = payload.get("user_id")
    roles = payload.get("roles", [])
    logger.debug(f"JWT decoded: user_id={user_id}, roles={roles}")
    
    if not user_id:
        logger.warning("Authentication failed: Missing user_id in token payload")
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"Authentication failed: User {user_id} not found")
        raise HTTPException(
            status_code=401,
            detail="User not found or inactive"
        )
    
    if not user.is_active:
        logger.warning(f"Authentication failed: User {user.username} (id={user_id}) is inactive")
        raise HTTPException(
            status_code=401,
            detail="User not found or inactive"
        )
    
    logger.debug(f"User authenticated: {user.username} (id={user_id}, roles={user.roles})")
    return user


optional_security = HTTPBearer(auto_error=False)


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Return the logged-in user if a valid token was sent, otherwise None.
    For public endpoints that show extra data to admins (never raises).
    """
    if credentials is None:
        return None
    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Require ADMIN or SUPER_ADMIN role.
    This allows both ADMIN and SUPER_ADMIN to access admin endpoints.
    """
    logger.info(
        f"Admin access check: user={current_user.username}, "
        f"roles={current_user.roles}, is_admin={current_user.is_admin}"
    )
    
    if not current_user.is_admin:
        logger.warning(
            f"Admin access DENIED: user={current_user.username}, "
            f"roles={current_user.roles}"
        )
        raise HTTPException(
            status_code=403,
            detail="Admin access required. You must have ADMIN or SUPER_ADMIN role."
        )
    
    logger.info(f"Admin access GRANTED: user={current_user.username}")
    return current_user


def require_super_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Require SUPER_ADMIN role only.
    Use this for critical operations like website configuration.
    """
    logger.info(
        f"Super Admin access check: user={current_user.username}, "
        f"roles={current_user.roles}, is_super_admin={current_user.is_super_admin}"
    )
    
    if not current_user.is_super_admin:
        logger.warning(
            f"Super Admin access DENIED: user={current_user.username}, "
            f"roles={current_user.roles}"
        )
        raise HTTPException(
            status_code=403,
            detail="Super Admin access required."
        )
    
    logger.info(f"Super Admin access GRANTED: user={current_user.username}")
    return current_user


def require_trustee(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Require at least TRUSTEE role (TRUSTEE, ADMIN, or SUPER_ADMIN).
    Used for read-only access to sensitive resources like donors and members.
    """
    logger.info(
        f"Trustee access check: user={current_user.username}, "
        f"roles={current_user.roles}"
    )
    
    # Check if user has at least one valid role (TRUSTEE, ADMIN, or SUPER_ADMIN)
    valid_roles = {"TRUSTEE", "ADMIN", "SUPER_ADMIN"}
    user_roles = set(current_user.roles or [])
    has_valid_role = bool(user_roles & valid_roles)
    
    if not has_valid_role:
        logger.warning(
            f"Trustee access DENIED: user={current_user.username}, "
            f"roles={current_user.roles}"
        )
        raise HTTPException(
            status_code=403,
            detail="Trustee access required. You must have TRUSTEE, ADMIN, or SUPER_ADMIN role."
        )
    
    logger.debug(f"Trustee access GRANTED: user={current_user.username}")
    return current_user


# Legacy alias for backward compatibility
get_current_admin_user = require_admin
get_current_trustee_user = require_trustee


def get_pooja_repository(
    db: Session = Depends(get_db),
) -> PoojaRepository:
    return PoojaRepository(db)


def get_pooja_service(
    db: Session = Depends(get_db),
) -> PoojaService:
    repo = PoojaRepository(db)
    return PoojaService(repo)


def get_member_repository(
    db: Session = Depends(get_db),
) -> MemberRepository:
    return MemberRepository(db)


def get_member_service(
    db: Session = Depends(get_db),
) -> MemberService:
    repo = MemberRepository(db)
    return MemberService(repo)


def get_donor_repository(
    db: Session = Depends(get_db),
) -> DonorRepository:
    return DonorRepository(db)


def get_donor_service(
    db: Session = Depends(get_db),
) -> DonorService:
    repo = DonorRepository(db)
    return DonorService(repo)

def get_gallery_repository(
    db: Session = Depends(get_db),
) -> GalleryRepository:
    return GalleryRepository(db)

def get_gallery_service(
    db: Session = Depends(get_db),
) -> GalleryService:
    repo = GalleryRepository(db)
    return GalleryService(repo)

def get_seva_ticket_repository(
    db: Session = Depends(get_db),
) -> SevaTicketRepository:
    return SevaTicketRepository(db)

def get_seva_ticket_service(
    db: Session = Depends(get_db),
) -> SevaTicketService:
    ticket_repo = SevaTicketRepository(db)
    pooja_repo = PoojaRepository(db)
    return SevaTicketService(ticket_repo, pooja_repo)

def get_announcement_repository(
    db: Session = Depends(get_db),
) -> AnnouncementRepository:
    return AnnouncementRepository(db)


def get_announcement_service(
    db: Session = Depends(get_db),
) -> AnnouncementService:
    repo = AnnouncementRepository(db)
    return AnnouncementService(repo)


def get_festival_repository(
    db: Session = Depends(get_db),
) -> FestivalRepository:
    return FestivalRepository(db)


def get_festival_service(
    db: Session = Depends(get_db),
) -> FestivalService:
    repo = FestivalRepository(db)
    return FestivalService(repo)


def get_contact_repository(
    db: Session = Depends(get_db),
) -> ContactRepository:
    return ContactRepository(db)


def get_contact_service(
    db: Session = Depends(get_db),
) -> ContactService:
    repo = ContactRepository(db)
    return ContactService(repo)
