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
from app.models.abhishekam import ABHISHEKAM_VISIBILITY_DAYS
from app.services.abhishekam_service import MAX_CALENDAR_DAYS, AbhishekamService
from app.services.email_service import EmailService
from app.services.occasion_greeting_service import OccasionGreetingService
from app.services.otp_service import OtpService
from app.services.storage_service import StorageService
from app.services.turnstile_service import TurnstileService
from app.utils.dependencies import (
    AuditContext, get_abhishekam_service, get_audit, get_occasion_greeting_service, get_otp_service,
    get_storage_service, get_turnstile_service, require_permission,
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
    start: date,
    end: date,
    service: AbhishekamService = Depends(get_abhishekam_service),
):
    """Public: every day from `start` to `end` (inclusive) with how many of
    the DAILY_SLOT_CAP slots are taken - the rolling contribution-style grid."""
    if end < start or (end - start).days >= MAX_CALENDAR_DAYS:
        raise HTTPException(status_code=400, detail=f"Choose a range of 1 to {MAX_CALENDAR_DAYS} days.")
    response.headers["Cache-Control"] = "public, max-age=60"
    return service.calendar_range(start, end)


@router.get("/calendar/{day}", response_model=AbhishekamDayFlyer)
def get_abhishekam_day_flyer(
    response: Response,
    day: date,
    service: AbhishekamService = Depends(get_abhishekam_service),
):
    """Public: one day - the pop-up when a calendar square is clicked, and
    the data behind that date's public blessings page. PUBLIC+PAID bookings
    only; a PRIVATE or still-PENDING booking counts toward slots_used but
    never appears in `entries`."""
    response.headers["Cache-Control"] = "public, max-age=60"
    return service.day_flyer(day)


@router.post("", response_model=AbhishekamOut, status_code=201)
def create_abhishekam(
    payload: AbhishekamCreate,
    request: Request,
    service: AbhishekamService = Depends(get_abhishekam_service),
    otp_service: OtpService = Depends(get_otp_service),
    turnstile: TurnstileService = Depends(get_turnstile_service),
):
    """Public: book an Abhishekam slot. Gated on a verified email (see
    request-otp/verify-otp above). Always PENDING at Rs {amount} until staff
    collect payment at the temple counter - see /collect-payment."""
    if not abhishekam_booking_limiter.is_allowed(get_client_ip(request)):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    if not turnstile.verify(payload.turnstile_token, get_client_ip(request)):
        raise HTTPException(status_code=400, detail="Security check failed. Please reload and try again.")
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
        f"Once the fee is paid, on {abhishekam.occasion_date} we'll email you your blessing, and your "
        f"page will open at:\n{settings.FRONTEND_BASE_URL}/abhishekam/{abhishekam.id}\n\n"
        f"It stays up for {ABHISHEKAM_VISIBILITY_DAYS} days from that date.\n\n"
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
    the fee is paid and occasion_date has arrived - see
    AbhishekamService.personal_page."""
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
    greetings: OccasionGreetingService = Depends(get_occasion_greeting_service),
    audit: AuditContext = Depends(get_audit),
    admin_user: User = Depends(_manage),
):
    """Marks a PENDING booking as PAID once the devotee pays at the temple
    counter, and records the cash income. The blessing email itself goes out
    on occasion_date - right now, if that day has already arrived."""
    abhishekam = service.collect_payment(abhishekam_id, admin_user)
    audit.log("COLLECT_PAYMENT", "abhishekam", str(abhishekam.id),
              f"Collected payment for Abhishekam {abhishekam.reference_number}",
              {"amount": abhishekam.amount})
    today = date.today()
    if greetings.abhishekam_due(abhishekam, today):
        greetings.send_abhishekam(abhishekam)
    elif abhishekam.occasion_date > today:
        EmailService().send(
            abhishekam.email,
            f"Payment received: {abhishekam.reference_number}",
            f"Dear {abhishekam.devotee_name},\n\n"
            f"We've received your Rs. {abhishekam.amount} payment for your {abhishekam.occasion} "
            f"Abhishekam on {abhishekam.occasion_date}.\n\n"
            "On that day we'll email you your blessing, and your page will open at:\n"
            f"{settings.FRONTEND_BASE_URL}/abhishekam/{abhishekam.id}\n\n"
            "Thank you,\nSri Varasidhi Vinayaka Swamy Devasthanam, Thorur",
        )
    return abhishekam
