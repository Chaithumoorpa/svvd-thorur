"""Read side of seva bookings made for an occasion: a seva's public booking
calendar, a day's public blessings, and each devotee's own blessing page.

A booking holds its slot while not cancelled - paid or not, or more people
than daily_slot_cap could all be told "you're in" before any of them pays.
It appears publicly only once paid for (or free), and only if the devotee
chose to show it; the photo only for BLESSING_VISIBLE_DAYS from the seva date.
"""
from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.pooja import Pooja
from app.models.seva_ticket import PaymentStatus, SevaTicket, TicketStatus
from app.schemas.blessing import (
    BlessingEntry, BlessingStatus, PersonalBlessingOut, SevaCalendarDay, SevaDay,
)

BLESSING_VISIBLE_DAYS = 7  # blessing pages and photos stay up this long, from the seva date
MAX_CALENDAR_DAYS = 400  # one request covers the public grid's 365-day window, not arbitrary history
_SETTLED = (PaymentStatus.FREE, PaymentStatus.PAID)


def visible_until(day: date) -> date:
    """Last day (inclusive) a day's blessing pages and photos stay up."""
    return day + timedelta(days=BLESSING_VISIBLE_DAYS - 1)


def blessing_status(day: date, today: date) -> BlessingStatus:
    if today < day:
        return "upcoming"
    return "active" if today <= visible_until(day) else "archived"


class BlessingService:
    def __init__(self, db: Session):
        self.db = db

    def _seva(self, pooja_id: int) -> Pooja:
        pooja = self.db.query(Pooja).filter(Pooja.id == pooja_id, Pooja.is_active.is_(True)).first()
        if not pooja:
            raise HTTPException(status_code=404, detail="Seva not found")
        return pooja

    def calendar(self, pooja_id: int, start: date, end: date) -> List[SevaCalendarDay]:
        """Every day from `start` to `end` inclusive with its booking count -
        one grouped query, zero-filled for days nobody booked."""
        pooja = self._seva(pooja_id)
        rows = (
            self.db.query(SevaTicket.seva_date, func.count(SevaTicket.id))
            .filter(
                SevaTicket.seva_id == pooja.id,
                SevaTicket.seva_date.between(start, end),
                SevaTicket.status != TicketStatus.CANCELLED,
            )
            .group_by(SevaTicket.seva_date)
            .all()
        )
        counts = dict(rows)
        return [
            SevaCalendarDay(date=day, slots_used=counts.get(day, 0), slots_total=pooja.daily_slot_cap)
            for day in (start + timedelta(days=i) for i in range((end - start).days + 1))
        ]

    def day(self, pooja_id: int, day: date, today: Optional[date] = None) -> SevaDay:
        pooja = self._seva(pooja_id)
        status = blessing_status(day, today or date.today())
        tickets = (
            self.db.query(SevaTicket)
            .filter(SevaTicket.seva_id == pooja.id, SevaTicket.seva_date == day,
                    SevaTicket.status != TicketStatus.CANCELLED)
            .order_by(SevaTicket.created_at.asc())
            .all()
        )
        shown = [t for t in tickets if t.show_publicly and t.occasion and t.payment_status in _SETTLED]
        return SevaDay(
            date=day,
            slots_used=len(tickets),
            slots_total=pooja.daily_slot_cap,
            blessing_status=status,
            visible_until=visible_until(day),
            entries=[
                BlessingEntry(devotee_name=t.devotee_name, occasion=t.occasion,
                              photo_url=t.photo_url if status == "active" else None)
                for t in shown
            ],
        )

    def personal(self, ticket_id: UUID, today: Optional[date] = None) -> PersonalBlessingOut:
        """Unguessable link (the ticket's random UUID) that reveals nothing
        beyond seva/occasion/date until the seva is paid for and its date
        has arrived. Only exists for a booking made for an occasion."""
        ticket = self.db.query(SevaTicket).filter(SevaTicket.id == ticket_id).first()
        if not ticket or not ticket.occasion or ticket.status == TicketStatus.CANCELLED:
            raise HTTPException(status_code=404, detail="Blessing not found")
        base = {"seva_name": ticket.seva_name, "occasion": ticket.occasion, "seva_date": ticket.seva_date}
        if ticket.payment_status not in _SETTLED:
            return PersonalBlessingOut(status="pending", **base)
        status = blessing_status(ticket.seva_date, today or date.today())
        if status == "upcoming":
            return PersonalBlessingOut(status="scheduled", **base)
        if status == "archived":
            return PersonalBlessingOut(status="expired", **base)
        return PersonalBlessingOut(
            status="active", devotee_name=ticket.devotee_name, photo_url=ticket.photo_url,
            visible_until=visible_until(ticket.seva_date), **base,
        )
