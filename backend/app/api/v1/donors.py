from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from sqlalchemy.orm import Session

from app.core.pagination import PageParams, page_params, paginate, set_total
from app.core.rbac import Permission, has_permission
from app.core.security import create_access_token, decode_access_token
from app.models.user import User
from app.repositories.donor_repo import DonorRepository
from app.repositories.temple_repo import TempleRepository
from app.schemas.donor import (
    DonationCreate, DonationOut, DonationUpdate, DonorCreate, DonorOut, DonorUpdate, DonationType,
)
from app.schemas.payment import DONATION_ONLINE_MODE, DonationOrderIn, RazorpayConfirmIn, RazorpayOrderOut
from app.services.donation_receipt_service import DonationReceiptService
from app.services.donor_service import DonationService, DonorService, donor_to_out
from app.services.email_service import EmailService
from app.services.razorpay_service import RazorpayService
from app.services.turnstile_service import TurnstileService
from app.utils.dependencies import (
    AuditContext, get_audit, get_db, get_razorpay_service, get_turnstile_service, require_permission,
)
from app.utils.rate_limiter import enforce, get_client_ip, payment_order_limiter

DONATION_PAYMENT_PURPOSE = "donation_payment"
PAYMENT_TOKEN_TTL = timedelta(minutes=20)  # generous for a bank's own OTP step mid-checkout

router = APIRouter(tags=["Donors & Donations"])

_read_donors = require_permission(Permission.DONORS_READ)
_write_donors = require_permission(Permission.DONORS_WRITE)
_read_donations = require_permission(Permission.DONATIONS_READ)
_write_donations = require_permission(Permission.DONATIONS_WRITE)


def get_donor_service(db: Session = Depends(get_db)) -> DonorService:
    return DonorService(DonorRepository(db))


def get_donation_service(db: Session = Depends(get_db)) -> DonationService:
    return DonationService(db)


def _donation_out(donation) -> DonationOut:
    out = DonationOut.model_validate(donation)
    out.donor_name = donation.donor.name if donation.donor else None
    return out


# ------------------------------------------------------------------------- donors
@router.get("/donors", response_model=List[DonorOut])
def list_donors(
    response: Response,
    search: Optional[str] = Query(None, max_length=100),
    service: DonorService = Depends(get_donor_service),
    params: PageParams = Depends(page_params),
    user: User = Depends(_read_donors),
):
    """Private donor directory (TRUSTEE and above). PAN is masked for read-only roles."""
    rows, total = paginate(service.query_donors(search), params)
    set_total(response, total)
    reveal = has_permission(user.roles, Permission.DONORS_WRITE)
    return [donor_to_out(row, reveal) for row in rows]


@router.get("/donors/{donor_id}", response_model=DonorOut)
def get_donor(
    donor_id: int,
    service: DonorService = Depends(get_donor_service),
    user: User = Depends(_read_donors),
):
    return donor_to_out(service.get_donor_row(donor_id), has_permission(user.roles, Permission.DONORS_WRITE))


@router.post("/donors", response_model=DonorOut, status_code=201)
def create_donor(
    payload: DonorCreate,
    service: DonorService = Depends(get_donor_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_write_donors),
):
    donor = service.create_donor(payload)
    audit.log("CREATE", "donor", donor.id, f"Added donor {donor.name}")
    return donor_to_out(service.get_donor_row(donor.id), True)


@router.put("/donors/{donor_id}", response_model=DonorOut)
def update_donor(
    donor_id: int,
    payload: DonorUpdate,
    service: DonorService = Depends(get_donor_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_write_donors),
):
    donor = service.update_donor(donor_id, payload.model_dump(exclude_unset=True))
    audit.log("UPDATE", "donor", donor_id, f"Updated donor {donor.name}",
              {"fields": sorted(payload.model_dump(exclude_unset=True).keys())})
    return donor_to_out(service.get_donor_row(donor_id), True)


@router.delete("/donors/{donor_id}", response_model=DonorOut)
def delete_donor(
    donor_id: int,
    service: DonorService = Depends(get_donor_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_write_donors),
):
    """Soft delete: donation history is kept."""
    donor = service.delete_donor(donor_id)
    audit.log("DELETE", "donor", donor_id, f"Deactivated donor {donor.name}")
    return donor_to_out(service.get_donor_row(donor_id), True)


# ---------------------------------------------------------------------- donations
@router.get("/donations", response_model=List[DonationOut])
def list_donations(
    response: Response,
    donor_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    donation_type: Optional[DonationType] = None,
    service: DonationService = Depends(get_donation_service),
    params: PageParams = Depends(page_params),
    _: User = Depends(_read_donations),
):
    query = service.query(donor_id, start_date, end_date, donation_type.value if donation_type else None)
    items, total = paginate(query, params)
    set_total(response, total)
    return [_donation_out(d) for d in items]


@router.post("/donations", response_model=DonationOut, status_code=201)
def create_donation(
    payload: DonationCreate,
    service: DonationService = Depends(get_donation_service),
    audit: AuditContext = Depends(get_audit),
    user: User = Depends(_write_donations),
):
    donation = service.create(payload, user.id)
    audit.log("CREATE", "donation", donation.id, f"Recorded donation of Rs. {donation.amount} from donor #{donation.donor_id}",
              {"amount": donation.amount, "type": donation.donation_type, "mode": donation.payment_mode})
    out = _donation_out(donation)
    EmailService().notify_admin(
        f"New donation recorded: Rs. {donation.amount}",
        f"Donor: {out.donor_name or 'Unknown'}\nAmount: Rs. {donation.amount}\n"
        f"Type: {donation.donation_type}\nMode: {donation.payment_mode.value}\n"
        f"Recorded by user #{user.id}",
    )
    if donation.occasion and donation.donor and donation.donor.email:
        EmailService().send(
            donation.donor.email,
            f"Blessings on your {donation.occasion}",
            f"Dear {donation.donor.name},\n\n"
            f"On the occasion of your {donation.occasion}, Sri Varasidhi Vinayaka Swamy Devasthanam "
            "sends you and your family warm greetings and blessings.\n\n"
            f"Your donation of Rs. {donation.amount} has been received with your intentions for this occasion.\n\n"
            "Thank you,\nSVVD Thorur",
        )
    return out


@router.put("/donations/{donation_id}", response_model=DonationOut)
def update_donation(
    donation_id: int,
    payload: DonationUpdate,
    service: DonationService = Depends(get_donation_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_write_donations),
):
    donation = service.update(donation_id, payload)
    audit.log("UPDATE", "donation", donation_id, f"Updated donation #{donation_id}",
              payload.model_dump(exclude_unset=True))
    return _donation_out(donation)


@router.delete("/donations/{donation_id}", response_model=dict)
def delete_donation(
    donation_id: int,
    service: DonationService = Depends(get_donation_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_write_donations),
):
    """Blocked once a receipt has been issued - see DonationService.delete."""
    service.delete(donation_id)
    audit.log("DELETE", "donation", donation_id, f"Deleted donation #{donation_id}")
    return {"message": "Donation deleted"}


@router.post("/donations/{donation_id}/receipt", response_model=DonationOut)
def generate_receipt(
    donation_id: int,
    service: DonationService = Depends(get_donation_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_write_donations),
):
    """Issue (or return the already issued) receipt number for a donation."""
    donation = service.issue_receipt(donation_id)
    audit.log("RECEIPT", "donation", donation_id, f"Issued receipt {donation.receipt_number}")
    return _donation_out(donation)


@router.get("/donations/{donation_id}/receipt")
def download_receipt(
    donation_id: int,
    service: DonationService = Depends(get_donation_service),
    db: Session = Depends(get_db),
    _: User = Depends(_read_donations),
):
    """Receipt PDF. Authenticated (TRUSTEE+): receipts contain donor personal data."""
    donation = service.get(donation_id)
    if not donation.receipt_number:
        raise HTTPException(status_code=400, detail="Receipt has not been generated yet")
    pdf = DonationReceiptService.generate_receipt_pdf(donation, TempleRepository(db).get_active())
    service.archive_receipt(donation, pdf)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Receipt_{donation.receipt_number}.pdf"'},
    )


# ---------------------------------------------------------------- public: pay online
@router.post("/donations/public/order", response_model=RazorpayOrderOut)
def create_donation_payment_order(
    payload: DonationOrderIn,
    request: Request,
    razorpay: RazorpayService = Depends(get_razorpay_service),
    turnstile: TurnstileService = Depends(get_turnstile_service),
):
    """Step 1 of a public online donation (no sign-in, no staff involved -
    contrast with POST /donations above, which requires an existing donor_id
    and TRUSTEE+ auth). The amount comes from the devotee's own input here
    (there's no server-side price to check it against, unlike a seva), but
    is bounded and never trusted again after this - the confirm step below
    refunds nothing extra and books nothing more than what this order paid
    for. Nothing is written to the database until the payment is verified."""
    enforce(payment_order_limiter, get_client_ip(request), "Too many payment attempts. Please try again later.")
    if not turnstile.verify(payload.turnstile_token, get_client_ip(request)):
        raise HTTPException(status_code=400, detail="Security check failed. Please reload and try again.")

    order = razorpay.create_order(payload.amount, purpose=f"Donation: {payload.donation_type.value}")
    donation = payload.model_dump(mode="json", exclude={"turnstile_token"})
    token = create_access_token(
        {"purpose": DONATION_PAYMENT_PURPOSE, "order_id": order["order_id"], "donation": donation},
        expires_delta=PAYMENT_TOKEN_TTL,
    )
    return RazorpayOrderOut(**order, payment_token=token)


@router.post("/donations/public/confirm", response_model=DonationOut)
def confirm_donation_payment(
    payload: RazorpayConfirmIn,
    service: DonationService = Depends(get_donation_service),
    razorpay: RazorpayService = Depends(get_razorpay_service),
):
    """Step 2: verifies the payment_token from public/order and the payment
    itself, then records the donation - matched or created by phone (see
    DonationService.find_or_create_donor_by_phone) - and issues its receipt
    right away, since the money has already arrived."""
    claims = decode_access_token(payload.payment_token)
    if not claims or claims.get("purpose") != DONATION_PAYMENT_PURPOSE or claims.get("order_id") != payload.razorpay_order_id:
        raise HTTPException(status_code=400, detail="This payment session has expired. Please try again.")
    if not razorpay.verify_payment_signature(
        payload.razorpay_order_id, payload.razorpay_payment_id, payload.razorpay_signature
    ):
        raise HTTPException(status_code=400, detail="Payment could not be verified. Please contact the temple office.")

    data = DonationOrderIn.model_validate(claims["donation"])
    donor = service.find_or_create_donor_by_phone(
        data.donor_name, data.phone, data.email, data.pan_number, data.address,
    )
    method = razorpay.payment_method(payload.razorpay_payment_id)
    donation = service.create_public(
        donor, amount=data.amount, donation_type=data.donation_type.value, purpose=data.purpose,
        occasion=data.occasion, razorpay_payment_id=payload.razorpay_payment_id, razorpay_method=method,
    )
    out = _donation_out(donation)
    EmailService().notify_admin(
        f"New online donation: Rs. {donation.amount}",
        f"Donor: {donor.name}\nPhone: {donor.phone}\nAmount: Rs. {donation.amount}\n"
        f"Type: {donation.donation_type}\nReceipt: {donation.receipt_number}\n"
        f"Paid online via Razorpay, payment {payload.razorpay_payment_id}",
    )
    if donor.email:
        EmailService().send(
            donor.email,
            f"Thank you for your donation - receipt {donation.receipt_number}",
            f"Dear {donor.name},\n\n"
            f"Thank you for your generous donation of Rs. {donation.amount} to "
            "Sri Varasidhi Vinayaka Swamy Devasthanam, Thorur.\n\n"
            f"Receipt number: {donation.receipt_number}\n"
            f"Date: {donation.donated_on:%d-%m-%Y}\n\n"
            "This receipt number is recorded in the temple's accounts; the receipt itself is "
            "available from the temple office on request.\n\n"
            "May Sri Varasidhi Vinayaka Swamy bless you and your family.\n\n"
            "Thank you,\nSri Varasidhi Vinayaka Swamy Devasthanam, Thorur",
        )
    return out
