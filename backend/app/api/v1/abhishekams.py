from datetime import date
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.core.config import settings
from app.core.pagination import PageParams, page_params, paginate, set_total
from app.core.rbac import Permission
from app.models.user import User
from app.schemas.abhishekam import (
    AbhishekamCalendarDay, AbhishekamCreate, AbhishekamDayFlyer, AbhishekamOut, AbhishekamPersonalPageOut,
)
from app.schemas.otp import OtpRequest, OtpVerifyRequest, OtpVerifyResponse
from app.schemas.upload import UploadUrlRequest, UploadUrlResponse
from app.services.abhishekam_service import AbhishekamService
from app.services.email_service import EmailService
from app.services.otp_service import OtpService
from app.services.storage_service import StorageService
from app.utils.dependencies import (
    AuditContext, get_abhishekam_service, get_audit, get_otp_service, get_storage_service, require_permission,
)
from app.utils.rate_limiter import (
    abhishekam_booking_limiter, abhishekam_upload_limiter, enforce, get_client_ip, otp_request_limiter,
    otp_verify_limiter,
)

router = APIRouter(prefix="/abhishekams", tags=["Abhishekam"])

_manage = require_permission(Permission.TICKETS_MANAGE)


@router.post("/request-otp", response_model=dict)
def request_abhishekam_otp(
    payload: OtpRequest,
    request: Request,
    service: OtpService = Depends(get_otp_service),
):
    enforce(otp_request_limiter, get_client_ip(request), "Too many requests. Please try again later.")
    service.request_abhishekam_otp(payload.email)
    return {"message": "Verification code sent. Please check your email."}


@router.post("/verify-otp", response_model=OtpVerifyResponse)
def verify_abhishekam_otp(
    payload: OtpVerifyRequest,
    request: Request,
    service: OtpService = Depends(get_otp_service),
):
    enforce(otp_verify_limiter, get_client_ip(request), "Too many attempts. Please try again later.")
    return OtpVerifyResponse(booking_token=service.verify_abhishekam_otp(payload.email, payload.code))


@router.post("/upload-url", response_model=UploadUrlResponse)
def create_abhishekam_upload_url(
    payload: UploadUrlRequest,
    request: Request,
    storage: StorageService = Depends(get_storage_service),
):
    """Presigned S3 upload for the devotee's own occasion photo - public, but
    rate limited (no admin auth: nobody is signed in at this point in the
    flow). Uses a nested gallery/abhishekam prefix so the upload stays under
    the bucket policy's public-read gallery/* prefix, matching gallery and
    member photos."""
    enforce(abhishekam_upload_limiter, get_client_ip(request), "Too many upload attempts. Please try again later.")
    return storage.create_upload(payload.content_type, key_prefix="gallery/abhishekam")


@router.get("/calendar", response_model=List[AbhishekamCalendarDay])
def get_abhishekam_calendar(
    response: Response,
    year: int,
    service: AbhishekamService = Depends(get_abhishekam_service),
):
    """Public: every day of `year` with how many of the DAILY_SLOT_CAP slots
    are taken - the 365-day grid, replicating the temple's paper register."""
    response.headers["Cache-Control"] = "public, max-age=60"
    return service.calendar_year(year)


@router.get("/calendar/{day}", response_model=AbhishekamDayFlyer)
def get_abhishekam_day_flyer(
    day: date,
    service: AbhishekamService = Depends(get_abhishekam_service),
):
    """Public: the flyer shown when a calendar day is clicked - PUBLIC+PAID
    bookings only (name, occasion, photo). A PRIVATE or still-PENDING
    booking still counts toward slots_used but never appears in `entries`."""
    return service.day_flyer(day)


@router.post("", response_model=AbhishekamOut, status_code=201)
def create_abhishekam(
    payload: AbhishekamCreate,
    request: Request,
    service: AbhishekamService = Depends(get_abhishekam_service),
    otp_service: OtpService = Depends(get_otp_service),
):
    """Public: book an Abhishekam slot. Gated on a verified email (see
    request-otp/verify-otp above). Always PENDING at Rs {amount} until staff
    collect payment at the temple counter - see /collect-payment."""
    if not abhishekam_booking_limiter.is_allowed(get_client_ip(request)):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    OtpService.check_abhishekam_token(payload.booking_token, payload.email)
    abhishekam = service.create(payload)
    EmailService().send(
        abhishekam.email,
        f"Abhishekam booking received: {abhishekam.reference_number}",
        f"Dear {abhishekam.devotee_name},\n\n"
        f"Your Abhishekam booking for {abhishekam.occasion_date} (occasion: {abhishekam.occasion}) "
        "has been received.\n\n"
        f"Reference number: {abhishekam.reference_number}\n"
        f"Fee: Rs. {abhishekam.amount}, payable in cash at the temple counter.\n\n"
        "Once the temple collects the fee, your page will be ready at:\n"
        f"{settings.FRONTEND_BASE_URL}/abhishekam/{abhishekam.id}\n\n"
        "It stays visible there for 7 days from the day payment is collected.\n\n"
        "Thank you,\nSri Varasidhi Vinayaka Swamy Devasthanam, Thorur",
    )
    return abhishekam


@router.get("/{abhishekam_id}/view", response_model=AbhishekamPersonalPageOut)
def view_abhishekam(
    abhishekam_id: UUID,
    service: AbhishekamService = Depends(get_abhishekam_service),
):
    """Public: the private link itself. Unguessable (a random UUID), but
    intentionally reveals nothing beyond the occasion/reference number until
    payment is collected - see AbhishekamService.personal_page."""
    return service.personal_page(abhishekam_id)


@router.get("", response_model=List[AbhishekamOut])
def list_abhishekams(
    response: Response,
    pending_only: bool = False,
    service: AbhishekamService = Depends(get_abhishekam_service),
    params: PageParams = Depends(page_params),
    _: User = Depends(_manage),
):
    query = service.query_pending() if pending_only else service.query_all()
    items, total = paginate(query, params)
    set_total(response, total)
    return items


@router.get("/{abhishekam_id}", response_model=AbhishekamOut)
def get_abhishekam(
    abhishekam_id: UUID,
    service: AbhishekamService = Depends(get_abhishekam_service),
    _: User = Depends(_manage),
):
    return service.get(abhishekam_id)


@router.post("/{abhishekam_id}/collect-payment", response_model=AbhishekamOut)
def collect_abhishekam_payment(
    abhishekam_id: UUID,
    service: AbhishekamService = Depends(get_abhishekam_service),
    audit: AuditContext = Depends(get_audit),
    admin_user: User = Depends(_manage),
):
    """Marks a PENDING booking as PAID once the devotee pays at the temple
    counter, and records the cash income."""
    abhishekam = service.collect_payment(abhishekam_id, admin_user)
    audit.log("COLLECT_PAYMENT", "abhishekam", str(abhishekam.id),
              f"Collected payment for Abhishekam {abhishekam.reference_number}",
              {"amount": abhishekam.amount})
    EmailService().send(
        abhishekam.email,
        f"Your Abhishekam page is ready: {abhishekam.reference_number}",
        f"Dear {abhishekam.devotee_name},\n\n"
        f"Payment for your {abhishekam.occasion} Abhishekam has been received - your page is "
        "now live:\n\n"
        f"{settings.FRONTEND_BASE_URL}/abhishekam/{abhishekam.id}\n\n"
        "It will be visible there for 7 days from today.\n\n"
        "Thank you,\nSri Varasidhi Vinayaka Swamy Devasthanam, Thorur",
    )
    return abhishekam
