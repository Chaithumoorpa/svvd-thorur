import html
import logging
import secrets
import qrcode
import io
import os
import base64
from datetime import date, datetime
from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from xhtml2pdf import pisa

from app.repositories.seva_ticket_repo import SevaTicketRepository
from app.repositories.pooja_repo import PoojaRepository
from app.schemas.seva_ticket import SevaBookingPublic, SevaTicketCreate, SevaTicketOut, SevaTicketFilter, TicketStatus, PaymentStatus, TicketSource
from app.models.seva_ticket import SevaTicket, TicketSource as ModelTicketSource
from app.models.finance import IncomeSourceType, IncomeTransaction, PaymentMode
from app.models.temple import Temple


class SevaTicketService:
    def __init__(self, ticket_repo: SevaTicketRepository, pooja_repo: PoojaRepository):
        self.ticket_repo = ticket_repo
        self.pooja_repo = pooja_repo

    def _generate_ticket_number(self) -> str:
        """Generates a human-readable ticket number: SVVD-YYYY-NNNNNN"""
        year = datetime.now().year
        prefix = f"SVVD-{year}-"
        
        last_number = self.ticket_repo.get_last_ticket_number(prefix)
        
        if not last_number:
            new_sequence = 1
        else:
            try:
                # Extract the sequence number from SVVD-YYYY-NNNNNN
                last_seq = int(last_number.split("-")[-1])
                new_sequence = last_seq + 1
            except (ValueError, IndexError):
                new_sequence = 1
                
        return f"{prefix}{new_sequence:06d}"

    def _generate_qr_token(self) -> str:
        """Generates a secure random QR token"""
        return secrets.token_urlsafe(32)

    def _create_with_unique_number(self, ticket_data: dict) -> SevaTicket:
        """Ticket numbers are sequential; retry if two bookings race for the same number."""
        for _ in range(5):
            ticket = SevaTicket(**ticket_data, ticket_number=self._generate_ticket_number(),
                                qr_token=self._generate_qr_token())
            try:
                return self.ticket_repo.create(ticket)
            except IntegrityError:
                self.ticket_repo.db.rollback()
        raise HTTPException(status_code=503, detail="Could not allocate a ticket number, please retry")

    def book_ticket(self, data: SevaBookingPublic) -> SevaTicket:
        pooja = self.pooja_repo.get_by_id(data.seva_id)
        if not pooja or not pooja.is_active:
            raise HTTPException(status_code=400, detail="Invalid or inactive Seva selected")
        if pooja.is_paid:
            # No online payment yet: never mint a paid ticket from an unauthenticated request.
            raise HTTPException(
                status_code=400,
                detail="This seva has a fee. Please book it at the temple counter.",
            )
        if data.seva_date < date.today():
            raise HTTPException(status_code=400, detail="Seva date cannot be in the past")
        if self.ticket_repo.check_duplicate(data.mobile_number, data.seva_date, data.seva_id):
            raise HTTPException(
                status_code=400,
                detail=f"A ticket for this Seva is already booked for this mobile number on {data.seva_date}",
            )

        return self._create_with_unique_number({
            "seva_id": pooja.id,
            "seva_name": pooja.name,          # from the database, not the client
            "devotee_name": data.devotee_name,
            "mobile_number": data.mobile_number,
            "seva_date": data.seva_date,
            "seva_time": data.seva_time,
            "payment_status": PaymentStatus.FREE,
            "amount": 0,
            "status": TicketStatus.ACTIVE,
            "source": ModelTicketSource.ONLINE,
        })

    def create_counter_ticket(self, data: SevaTicketCreate, admin_user) -> SevaTicket:
        """Manual ticket from the temple counter; records the staff member who issued it."""
        pooja = self.pooja_repo.get_by_id(data.seva_id)
        if not pooja:
            raise HTTPException(status_code=400, detail="Invalid Seva selected")

        ticket = self._create_with_unique_number({
            "seva_id": pooja.id,
            "seva_name": data.seva_name or pooja.name,
            "devotee_name": data.devotee_name,
            "mobile_number": data.mobile_number,
            "seva_date": data.seva_date,
            "seva_time": data.seva_time,
            "payment_status": data.payment_status,
            "amount": data.amount,
            "status": TicketStatus.ACTIVE,
            "source": ModelTicketSource.COUNTER,
            "created_by_admin_id": admin_user.id,
        })

        if ticket.payment_status == PaymentStatus.PAID and ticket.amount and ticket.amount > 0:
            # Counter tickets are collected in cash today; PaymentMode will need
            # to come from the ticket itself once online payment (Razorpay) lands.
            self.ticket_repo.db.add(IncomeTransaction(
                source_type=IncomeSourceType.SEVA,
                reference_id=f"seva_ticket:{ticket.id}",
                amount=ticket.amount,
                payment_mode=PaymentMode.CASH,
                received_by=admin_user.id,
                notes=f"Seva ticket {ticket.ticket_number} - {ticket.seva_name} ({ticket.devotee_name})",
            ))
            self.ticket_repo.db.commit()

        return ticket

    def query_tickets(self, filters: SevaTicketFilter):
        return self.ticket_repo.query_tickets(
            seva_id=filters.seva_id, seva_date=filters.seva_date,
            status=filters.status, mobile_number=filters.mobile_number,
        )

    def list_tickets(self, filters: SevaTicketFilter) -> List[SevaTicket]:
        return self.ticket_repo.list_tickets(
            seva_id=filters.seva_id,
            seva_date=filters.seva_date,
            status=filters.status,
            mobile_number=filters.mobile_number
        )

    def get_ticket(self, ticket_id: UUID) -> SevaTicket:
        ticket = self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return ticket

    def scan_ticket(self, identifier: str) -> SevaTicket:
        """
        Scans a ticket using either the QR token (secure) or the ticket number (manual entry).
        Marks it as USED if currently ACTIVE.
        """
        # 1. Try by QR Token first
        ticket = self.ticket_repo.get_by_qr_token(identifier)
        
        # 2. Fallback to Ticket Number if not found by QR token
        if not ticket:
            ticket = self.ticket_repo.get_by_ticket_number(identifier)
            
        if not ticket:
            raise HTTPException(status_code=404, detail="Invalid QR code or Ticket Number")
            
        if ticket.status == TicketStatus.USED:
            raise HTTPException(status_code=400, detail="Ticket has already been used")
            
        if ticket.status == TicketStatus.CANCELLED:
            raise HTTPException(status_code=400, detail="Ticket has been cancelled")

        # Mark as used
        return self.ticket_repo.update_status(ticket, TicketStatus.USED)

    def _get_logo_base64(self) -> Optional[str]:
        """Reads the temple logo and returns it as base64"""
        try:
            # Try multiple possible paths for robustness
            paths = [
                "assets/logo.png",
                "/app/assets/logo.png",
                "../frontend/public/logo.png"
            ]
            for path in paths:
                if os.path.exists(path):
                    with open(path, "rb") as image_file:
                        return base64.b64encode(image_file.read()).decode()
            return None
        except Exception:
            return None

    def generate_qr_base64(self, qr_token: str) -> str:
        """Generates a base64 encoded QR code image for the token"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_token)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

    def generate_ticket_html(self, ticket: SevaTicket) -> str:
        """Generates redundant HTML template optimized for 80mm mini-printers"""
        qr_base64 = self.generate_qr_base64(ticket.qr_token)
        logo_base64 = self._get_logo_base64()
        display_date = ticket.seva_date.strftime("%d-%m-%Y")
        display_time = ticket.seva_time.strftime("%I:%M %p") if ticket.seva_time else "N/A"

        temple = self.ticket_repo.db.query(Temple).first()
        temple_name = html.escape(temple.name) if temple and temple.name else "Sri Varasiddhi Vinayaka Swamy Devasthanam"
        temple_loc = html.escape(", ".join(
            p for p in [temple.village, temple.district, temple.state] if p
        )) if temple else "Thorur, Andhra Pradesh"

        logo_html = f'<img class="watermark" src="data:image/png;base64,{logo_base64}" />' if logo_base64 else ''
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {{ 
                    size: 80mm 200mm; 
                    margin: 4mm;
                }}
                body {{ 
                    font-family: Helvetica, Arial, sans-serif; 
                    margin: 0; padding: 0; color: #000;
                    width: 72mm;
                }}
                .ticket {{ 
                    width: 100%; position: relative; background: #fff;
                    padding: 5px;
                }}
                .watermark {{
                    position: absolute;
                    top: 15%;
                    left: 10%;
                    width: 80%;
                    opacity: 0.1;
                    z-index: -1;
                }}
                .header {{ text-align: center; border-bottom: 1px solid #000; padding-bottom: 5px; margin-bottom: 10px; }}
                .temple-name {{ font-size: 16px; font-weight: bold; margin: 0; text-transform: uppercase; }}
                .temple-loc {{ font-size: 11px; margin: 2px 0; }}
                .ticket-title {{ font-size: 14px; font-weight: bold; margin-top: 5px; text-decoration: underline; }}
                
                .content {{ margin-bottom: 15px; }}
                .row {{ clear: both; margin-bottom: 4px; border-bottom: 1px dotted #ccc; padding-bottom: 2px; display: block; }}
                .label {{ font-weight: bold; width: 40%; float: left; font-size: 11px; }}
                .value {{ font-weight: bold; float: left; width: 60%; font-size: 11px; }}
                
                .qr-container {{ text-align: center; margin-top: 10px; clear: both; }}
                .qr-code {{ width: 100px; height: 100px; }}
                .ticket-num {{ font-family: monospace; font-size: 13px; font-weight: bold; margin-top: 3px; }}
                
                .footer {{ text-align: center; font-size: 9px; margin-top: 15px; border-top: 1px solid #000; padding-top: 5px; }}
                .status-badge {{ 
                    text-align: center; font-size: 12px; font-weight: bold;
                    border: 1px solid #000; width: 50%; margin: 0 auto 10px auto; padding: 2px;
                }}
            </style>
        </head>
        <body>
            <div class="ticket">
                {logo_html}
                <div class="header">
                    <div class="temple-name">{temple_name}</div>
                    <div class="temple-loc">{temple_loc}</div>
                    <div class="ticket-title">SEVA TICKET</div>
                </div>

                <div class="status-badge">{ticket.status.value}</div>
                
                <div class="content">
                    <div class="row"><span class="label">Ticket #:</span> <span class="value">{ticket.ticket_number}</span></div>
                    <div class="row"><span class="label">Devotee:</span> <span class="value">{html.escape(ticket.devotee_name)}</span></div>
                    <div class="row"><span class="label">Seva:</span> <span class="value">{html.escape(ticket.seva_name)}</span></div>
                    <div class="row"><span class="label">Date:</span> <span class="value">{display_date}</span></div>
                    <div class="row"><span class="label">Time:</span> <span class="value">{display_time}</span></div>
                    <div class="row"><span class="label">Fee:</span> <span class="value">Rs. {ticket.amount} ({ticket.payment_status.value})</span></div>
                </div>
                
                <div class="qr-container">
                    <img class="qr-code" src="data:image/png;base64,{qr_base64}" alt="QR" />
                    <div class="ticket-num">{ticket.ticket_number}</div>
                </div>
                
                <div class="footer">
                    <p>Printed: {datetime.now().strftime("%d-%m-%Y %H:%M")}</p>
                    <p>Valid for one-time use only. No cancellations.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def generate_ticket_pdf(self, ticket: SevaTicket) -> io.BytesIO:
        """Generates a PDF file for the ticket"""
        html = self.generate_ticket_html(ticket)
        result = io.BytesIO()
        pdf = pisa.pisaDocument(io.BytesIO(html.encode("utf-8")), result)

        if pdf.err:
            raise HTTPException(status_code=500, detail="Error generating PDF ticket")

        result.seek(0)
        return result

    def archive_ticket_pdf(self, ticket: SevaTicket, pdf_bytes: bytes) -> None:
        """Best-effort S3 archive of a generated ticket PDF. Never raises - a
        storage hiccup must not block the admin from getting their PDF."""
        from app.services.storage_service import StorageService

        storage = StorageService()
        if not storage.enabled:
            return
        try:
            key = storage.upload_private(
                pdf_bytes, f"tickets/{ticket.ticket_number}.pdf", "application/pdf"
            )
            self.ticket_repo.save_pdf_key(ticket, key)
        except Exception:
            logging.getLogger(__name__).warning(
                "Failed to archive ticket PDF to S3 for %s", ticket.ticket_number, exc_info=True
            )
