from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.core.config import settings
from app.core.pagination import PageParams, page_params, paginate, set_total
from app.core.rbac import Permission
from app.models.user import User
from app.schemas.occasion_blessing import (
    OccasionBlessingCreate, OccasionBlessingOut, OccasionBlessingPublicOut,
)
from app.schemas.otp import OtpRequest, OtpVerifyRequest, OtpVerifyResponse
from app.schemas.upload import UploadUrlRequest, UploadUrlResponse
from app.services.email_service import EmailService
from app.services.occasion_blessing_service import OccasionBlessingService
from app.services.otp_service import OtpService
from app.services.storage_service import StorageService
from app.utils.dependencies import (
    AuditContext, get_audit, get_occasion_blessing_service, get_otp_service, get_storage_service,
    require_permission,
)
from app.utils.rate_limiter import (
    enforce, get_client_ip, occasion_blessing_limiter, occasion_upload_limiter, otp_request_limiter,
    otp_verify_limiter,
)

router = APIRouter(prefix="/occasion-blessings", tags=["Occasion Blessings"])

_manage = require_permission(Permission.TICKETS_MANAGE)


@router.post("/request-otp", response_model=dict)
def request_occasion_otp(
    payload: OtpRequest,
    request: Request,
    service: OtpService = Depends(get_otp_service),
):
    enforce(otp_request_limiter, get_client_ip(request), "Too many requests. Please try again later.")
    service.request_occasion_otp(payload.email)
    return {"message": "Verification code sent. Please check your email."}


@router.post("/verify-otp", response_model=OtpVerifyResponse)
def verify_occasion_otp(
    payload: OtpVerifyRequest,
    request: Request,
    service: OtpService = Depends(get_otp_service),
):
    enforce(otp_verify_limiter, get_client_ip(request), "Too many attempts. Please try again later.")
    return OtpVerifyResponse(booking_token=service.verify_occasion_otp(payload.email, payload.code))


@router.post("/upload-url", response_model=UploadUrlResponse)
def create_occasion_upload_url(
    payload: UploadUrlRequest,
    request: Request,
    storage: StorageService = Depends(get_storage_service),
):
    """Presigned S3 upload for the devotee's own occasion photo - public, but
    rate limited (no admin auth: nobody is signed in at this point in the
    flow). Uses a nested gallery/occasions prefix so the upload stays under
    the bucket policy's public-read gallery/* prefix, matching gallery and
    member photos - the page itself stays gated on payment, not on this
    upload being hard to reach."""
    enforce(occasion_upload_limiter, get_client_ip(request), "Too many upload attempts. Please try again later.")
    return storage.create_upload(payload.content_type, key_prefix="gallery/occasions")


@router.post("", response_model=OccasionBlessingOut, status_code=201)
def create_occasion_blessing(
    payload: OccasionBlessingCreate,
    request: Request,
    service: OccasionBlessingService = Depends(get_occasion_blessing_service),
    otp_service: OtpService = Depends(get_otp_service),
):
    """Public: submit an Occasion Blessing request. Gated on a verified email
    (see request-otp/verify-otp above). Always PENDING at Rs {amount} until
    staff collect payment at the temple counter - see /collect-payment."""
    if not occasion_blessing_limiter.is_allowed(get_client_ip(request)):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    OtpService.check_occasion_token(payload.booking_token, payload.email)
    blessing = service.create(payload)
    EmailService().send(
        blessing.email,
        f"Occasion Blessing request received: {blessing.reference_number}",
        f"Dear {blessing.devotee_name},\n\n"
        f"Your Occasion Blessing request for your {blessing.occasion} has been received.\n\n"
        f"Reference number: {blessing.reference_number}\n"
        f"Fee: Rs. {blessing.amount}, payable in cash at the temple counter.\n\n"
        "Once the temple collects the fee, your page will be ready at:\n"
        f"{settings.FRONTEND_BASE_URL}/blessings/{blessing.id}\n\n"
        "It stays visible there for 7 days from the day payment is collected.\n\n"
        "Thank you,\nSri Varasidhi Vinayaka Swamy Devasthanam, Thorur",
    )
    return blessing


@router.get("/{blessing_id}/view", response_model=OccasionBlessingPublicOut)
def view_occasion_blessing(
    blessing_id: UUID,
    service: OccasionBlessingService = Depends(get_occasion_blessing_service),
):
    """Public: the private link itself. Unguessable (a random UUID), but
    intentionally reveals nothing beyond the occasion/reference number until
    payment is collected - see OccasionBlessingService.public_view."""
    return service.public_view(blessing_id)


@router.get("", response_model=List[OccasionBlessingOut])
def list_occasion_blessings(
    response: Response,
    pending_only: bool = False,
    service: OccasionBlessingService = Depends(get_occasion_blessing_service),
    params: PageParams = Depends(page_params),
    _: User = Depends(_manage),
):
    query = service.query_pending() if pending_only else service.query_all()
    items, total = paginate(query, params)
    set_total(response, total)
    return items


@router.get("/{blessing_id}", response_model=OccasionBlessingOut)
def get_occasion_blessing(
    blessing_id: UUID,
    service: OccasionBlessingService = Depends(get_occasion_blessing_service),
    _: User = Depends(_manage),
):
    return service.get(blessing_id)


@router.post("/{blessing_id}/collect-payment", response_model=OccasionBlessingOut)
def collect_occasion_blessing_payment(
    blessing_id: UUID,
    service: OccasionBlessingService = Depends(get_occasion_blessing_service),
    audit: AuditContext = Depends(get_audit),
    admin_user: User = Depends(_manage),
):
    """Marks a PENDING request as PAID once the devotee pays at the temple
    counter, and records the cash income."""
    blessing = service.collect_payment(blessing_id, admin_user)
    audit.log("COLLECT_PAYMENT", "occasion_blessing", str(blessing.id),
              f"Collected payment for Occasion Blessing {blessing.reference_number}",
              {"amount": blessing.amount})
    EmailService().send(
        blessing.email,
        f"Your Occasion Blessing page is ready: {blessing.reference_number}",
        f"Dear {blessing.devotee_name},\n\n"
        f"Payment for your {blessing.occasion} Occasion Blessing has been received - your page is "
        "now live:\n\n"
        f"{settings.FRONTEND_BASE_URL}/blessings/{blessing.id}\n\n"
        "It will be visible there for 7 days from today.\n\n"
        "Thank you,\nSri Varasidhi Vinayaka Swamy Devasthanam, Thorur",
    )
    return blessing
