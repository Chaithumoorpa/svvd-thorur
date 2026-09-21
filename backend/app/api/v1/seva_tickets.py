from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime

from app.core.pagination import PageParams, page_params, paginate, set_total
from app.core.rbac import Permission
from app.utils.dependencies import AuditContext, get_audit, get_seva_ticket_service, require_permission
from app.utils.rate_limiter import booking_limiter, get_client_ip
from app.services.seva_ticket_service import SevaTicketService
from app.schemas.seva_ticket import (
    SevaBookingPublic,
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


@router.post("", response_model=SevaTicketOut)
def book_seva_ticket(
    payload: SevaBookingPublic,
    request: Request,
    service: SevaTicketService = Depends(get_seva_ticket_service),
):
    """
    Public endpoint to book a FREE seva. Price/payment/seva name are decided server-side.
    Rate limited per IP.
    """
    if not booking_limiter.is_allowed(get_client_ip(request)):
        raise HTTPException(status_code=429, detail="Too many bookings. Please try again later.")
    return service.book_ticket(payload)


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
