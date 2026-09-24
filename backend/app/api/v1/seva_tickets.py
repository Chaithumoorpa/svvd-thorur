from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime

from app.core.pagination import PageParams, page_params, paginate, set_total
from app.core.rbac import Permission
from app.utils.dependencies import (
    AuditContext, get_audit, get_current_user, get_current_user_optional, get_otp_service,
    get_seva_ticket_service, require_admin, require_permission,
)
from app.utils.rate_limiter import booking_limiter, enforce, get_client_ip, otp_request_limiter, otp_verify_limiter
from app.services.email_service import EmailService
from app.services.otp_service import OtpService
from app.services.seva_ticket_service import SevaTicketService
from app.schemas.otp import OtpRequest, OtpVerifyRequest, OtpVerifyResponse
from app.schemas.seva_ticket import (
    SevaBookingOnline,
    SevaTicketCreate,
    SevaTicketOut,
    SevaTicketFilter,
    ScanRequest,
    ScanResponse,
    TicketStatus
)
from app.models.user import User

router = APIRouter(prefix="/seva-tickets", tags=["Seva Tickets"])

_manage = require_permission(Permission.TICKETS_MANAGE)


@router.post("/booking/request-otp", response_model=dict)
def request_booking_otp(
    payload: OtpRequest,
    request: Request,
    service: OtpService = Depends(get_otp_service),
):
    """Emails a 6-digit code (valid 10 minutes) to verify a devotee's email
    before an online booking. Rate limited per IP."""
    enforce(otp_request_limiter, get_client_ip(request), "Too many requests. Please try again later.")
    service.request_otp(payload.email)
    return {"message": "Verification code sent. Please check your email."}


@router.post("/booking/verify-otp", response_model=OtpVerifyResponse)
def verify_booking_otp(
    payload: OtpVerifyRequest,
    request: Request,
    service: OtpService = Depends(get_otp_service),
):
    """Verifies the code and returns a short-lived token proving this email was
    verified, required by POST /seva-tickets for this same email. Rate limited
    per IP; the code itself allows only 5 incorrect guesses before it's dead."""
    enforce(otp_verify_limiter, get_client_ip(request), "Too many attempts. Please try again later.")
    return OtpVerifyResponse(booking_token=service.verify_otp(payload.email, payload.code))


@router.post("", response_model=SevaTicketOut)
def book_seva_ticket(
    payload: SevaBookingOnline,
    request: Request,
    service: SevaTicketService = Depends(get_seva_ticket_service),
    current_user: User | None = Depends(get_current_user_optional),
):
    """
    Public endpoint to book a FREE seva, gated on a verified email (see the
    booking/request-otp and booking/verify-otp endpoints above). Price/payment/
    seva name are decided server-side. Rate limited per IP. When the devotee
    happens to be signed in, the ticket is linked to their account (My Bookings);
    booking works the same either way, signed in is never required.
    """
    if not booking_limiter.is_allowed(get_client_ip(request)):
        raise HTTPException(status_code=429, detail="Too many bookings. Please try again later.")
    OtpService.check_booking_token(payload.booking_token, payload.email)
    ticket = service.book_ticket(payload, booked_by_user_id=current_user.id if current_user else None)
    EmailService().notify_admin(
        f"New seva booking: {ticket.seva_name} ({ticket.ticket_number})",
        f"Devotee: {ticket.devotee_name}\nMobile: {ticket.mobile_number}\nEmail: {ticket.email}\n"
        f"Seva: {ticket.seva_name}\nDate: {ticket.seva_date}\nTicket: {ticket.ticket_number}",
    )
    payment_note = (
        f"This seva has a fee of Rs. {ticket.amount}, payable in cash at the temple counter "
        "when you arrive.\n\n"
        if ticket.payment_status.value == "PENDING" else ""
    )
    EmailService().send(
        ticket.email,
        f"Booking confirmed: {ticket.seva_name} ({ticket.ticket_number})",
        f"Dear {ticket.devotee_name},\n\n"
        f"Your seva booking is confirmed.\n\n"
        f"Ticket number: {ticket.ticket_number}\n"
        f"Seva: {ticket.seva_name}\n"
        f"Date: {ticket.seva_date}\n\n"
        f"{payment_note}"
        "Please show this ticket number at the temple counter.\n\n"
        "Thank you,\nSri Varasiddhi Vinayaka Swamy Devasthanam, Thorur",
    )
    return ticket


@router.post("/admin", response_model=SevaTicketOut)
def create_admin_seva_ticket(
    payload: SevaTicketCreate,
    service: SevaTicketService = Depends(get_seva_ticket_service),
    audit: AuditContext = Depends(get_audit),
    admin_user: User = Depends(_manage),
):
    """Counter ticket (staff). Requires the tickets:manage permission."""
    ticket = service.create_counter_ticket(payload, admin_user)
    audit.log("CREATE", "seva_ticket", ticket.id, f"Issued counter ticket {ticket.ticket_number}",
              {"amount": ticket.amount, "payment": ticket.payment_status})
    return ticket


@router.get("", response_model=List[SevaTicketOut])
def list_seva_tickets(
    response: Response,
    seva_id: Optional[int] = None,
    seva_date: Optional[date] = None,
    status: Optional[TicketStatus] = None,
    mobile: Optional[str] = Query(None, max_length=20),
    service: SevaTicketService = Depends(get_seva_ticket_service),
    params: PageParams = Depends(page_params),
    _: User = Depends(_manage),
):
    """Paginated ticket list with filters (tickets:manage)."""
    filters = SevaTicketFilter(seva_id=seva_id, seva_date=seva_date, status=status, mobile_number=mobile)
    items, total = paginate(service.query_tickets(filters), params)
    set_total(response, total)
    return items


@router.get("/mine", response_model=List[SevaTicketOut])
def list_my_tickets(
    service: SevaTicketService = Depends(get_seva_ticket_service),
    current_user: User = Depends(get_current_user),
):
    """The signed-in devotee's own bookings (My Bookings) - only ones made while
    logged in are linked; anonymous online bookings and counter tickets are not."""
    return service.list_for_user(current_user.id)


@router.post("/{ticket_id}/collect-payment", response_model=SevaTicketOut)
def collect_ticket_payment(
    ticket_id: UUID,
    service: SevaTicketService = Depends(get_seva_ticket_service),
    audit: AuditContext = Depends(get_audit),
    admin_user: User = Depends(_manage),
):
    """Marks a PENDING ticket (a paid seva booked online, fee not yet collected)
    as PAID once the devotee pays in person, and records the cash income."""
    ticket = service.collect_payment(ticket_id, admin_user)
    audit.log("COLLECT_PAYMENT", "seva_ticket", ticket.id, f"Collected payment for ticket {ticket.ticket_number}",
              {"amount": ticket.amount})
    return ticket


@router.delete("/{ticket_id}")
def delete_seva_ticket(
    ticket_id: UUID,
    service: SevaTicketService = Depends(get_seva_ticket_service),
    audit: AuditContext = Depends(get_audit),
    admin_user: User = Depends(require_admin),
):
    """Admin/Super Admin only - deliberately narrower than tickets:manage (which
    STAFF also holds), since deleting also removes any linked finance entry."""
    ticket = service.get_ticket(ticket_id)
    audit.log("DELETE", "seva_ticket", ticket.id, f"Deleted ticket {ticket.ticket_number}",
              {"seva": ticket.seva_name, "amount": ticket.amount, "payment": ticket.payment_status})
    service.delete_ticket(ticket_id)
    return {"message": "Ticket deleted"}


@router.get("/{ticket_id}", response_model=SevaTicketOut)
def get_ticket_details(
    ticket_id: UUID,
    service: SevaTicketService = Depends(get_seva_ticket_service),
    _: User = Depends(_manage),
):
    """
    Admin endpoint to view ticket details.
    """
    return service.get_ticket(ticket_id)


@router.post("/scan", response_model=ScanResponse)
def scan_ticket(
    payload: ScanRequest,
    service: SevaTicketService = Depends(get_seva_ticket_service),
    audit: AuditContext = Depends(get_audit),
    admin_user: User = Depends(_manage),
):
    """
    Admin endpoint to scan and validate a QR code.
    Mark ticket as USED if valid.
    """
    try:
        ticket = service.scan_ticket(payload.qr_token)
        audit.log("SCAN", "seva_ticket", ticket.id, f"Scanned ticket {ticket.ticket_number}")
        return ScanResponse(
            success=True,
            message="Ticket successfully validated and marked as USED",
            ticket=ticket
        )
    except HTTPException as e:
        return ScanResponse(
            success=False,
            message=e.detail,
            ticket=None
        )


@router.get("/{ticket_id}/print", response_class=HTMLResponse)
def print_ticket(
    ticket_id: UUID,
    service: SevaTicketService = Depends(get_seva_ticket_service),
    _: User = Depends(_manage),
):
    """
    Admin endpoint to generate a printable ticket (HTML view).
    """
    ticket = service.get_ticket(ticket_id)
    html_content = service.generate_ticket_html(ticket)
    # Add a print script to the HTML if viewed in browser
    html_content = html_content.replace("</body>", '<div style="text-align: center; margin-top: 20px;"><button onclick="window.print()" style="padding: 10px 20px; cursor: pointer; background: #e74c3c; color: white; border: none; border-radius: 5px;">Print Ticket</button></div></body>')
    return HTMLResponse(content=html_content)


@router.get("/{ticket_id}/pdf")
def get_ticket_pdf(
    ticket_id: UUID,
    action: str = Query("print", enum=["download", "print"]),
    service: SevaTicketService = Depends(get_seva_ticket_service),
    _: User = Depends(_manage),
):
    """
    Admin endpoint to generate a PDF ticket.
    action="download" triggers a file download.
    action="print" (default) allows inline viewing/printing.
    """
    ticket = service.get_ticket(ticket_id)
    pdf_content = service.generate_ticket_pdf(ticket)
    service.archive_ticket_pdf(ticket, pdf_content.getvalue())

    filename = f"ticket_{ticket.ticket_number}.pdf"
    content_disposition = "attachment" if action == "download" else "inline"
    
    return Response(
        content=pdf_content.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"{content_disposition}; filename={filename}"
        }
    )
