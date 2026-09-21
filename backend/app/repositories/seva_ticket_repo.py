from sqlalchemy.orm import Session
from sqlalchemy import and_
from uuid import UUID
from datetime import date
from typing import List, Optional

from app.models.seva_ticket import SevaTicket, TicketStatus
from app.repositories.base import BaseRepository


class SevaTicketRepository(BaseRepository):
    def create(self, ticket: SevaTicket) -> SevaTicket:
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def get_by_id(self, ticket_id: UUID) -> Optional[SevaTicket]:
        return self.db.query(SevaTicket).filter(SevaTicket.id == ticket_id).first()

    def get_by_qr_token(self, qr_token: str) -> Optional[SevaTicket]:
        return self.db.query(SevaTicket).filter(SevaTicket.qr_token == qr_token).first()

    def get_by_ticket_number(self, ticket_number: str) -> Optional[SevaTicket]:
        from sqlalchemy import func
        return self.db.query(SevaTicket).filter(
            func.lower(SevaTicket.ticket_number) == ticket_number.lower()
        ).first()

    def query_tickets(
        self,
        seva_id: Optional[int] = None,
        seva_date: Optional[date] = None,
        status: Optional[TicketStatus] = None,
        mobile_number: Optional[str] = None,
    ):
        query = self.db.query(SevaTicket)
        if seva_id:
            query = query.filter(SevaTicket.seva_id == seva_id)
        if seva_date:
            query = query.filter(SevaTicket.seva_date == seva_date)
        if status:
            query = query.filter(SevaTicket.status == status)
        if mobile_number:
            query = query.filter(SevaTicket.mobile_number == mobile_number)
        return query.order_by(SevaTicket.created_at.desc(), SevaTicket.ticket_number.desc())

    def list_tickets(self, **filters) -> List[SevaTicket]:
        return self.query_tickets(**filters).all()

    def check_duplicate(self, mobile_number: str, seva_date: date, seva_id: int) -> bool:
        return self.db.query(SevaTicket).filter(
            and_(
                SevaTicket.mobile_number == mobile_number,
                SevaTicket.seva_date == seva_date,
                SevaTicket.seva_id == seva_id,
                SevaTicket.status != TicketStatus.CANCELLED
            )
        ).first() is not None

    def get_last_ticket_number(self, prefix: str) -> Optional[str]:
        """Returns the last used ticket number for a given prefix (e.g., SVVD-2025-)"""
        last_ticket = self.db.query(SevaTicket).filter(
            SevaTicket.ticket_number.like(f"{prefix}%")
        ).order_by(SevaTicket.ticket_number.desc()).first()
        
        return last_ticket.ticket_number if last_ticket else None

    def update_status(self, ticket: SevaTicket, status: TicketStatus) -> SevaTicket:
        ticket.status = status
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def save_pdf_key(self, ticket: SevaTicket, key: str) -> SevaTicket:
        ticket.pdf_s3_key = key
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def count(self) -> int:
        return self.db.query(SevaTicket).count()

    def count_today(self) -> int:
        return self.db.query(SevaTicket).filter(SevaTicket.seva_date == date.today()).count()
