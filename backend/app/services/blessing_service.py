"""Read side of seva bookings made for an occasion: a seva's public booking
calendar, a day's public blessings, and each devotee's own blessing page.

A booking holds its slot while not cancelled - paid or not, or more people
than daily_slot_cap could all be told "you're in" before any of them pays.
It appears publicly only once paid for (or free), only if the devotee chose
to show it, and only once staff have approved it - anyone with an email can
book, so nothing they submit goes on the website unreviewed. The photo shows
only for BLESSING_VISIBLE_DAYS from the seva date.
"""
import logging
from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.pooja import Pooja
from app.models.seva_ticket import PaymentStatus, ReviewStatus, SevaTicket, TicketStatus
from app.schemas.blessing import (
    BlessingEntry, BlessingReviewOut, BlessingStatus, PersonalBlessingOut, SevaCalendarDay, SevaDay,
)
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

BLESSING_VISIBLE_DAYS = 7  # blessing pages and photos stay up this long, from the seva date
MAX_CALENDAR_DAYS = 400  # one request covers the public grid's 365-day window, not arbitrary history
_SETTLED = (PaymentStatus.FREE, PaymentStatus.PAID)
PUBLIC_PHOTO_PREFIX = "gallery/blessings"  # public-read, like the photo gallery


def approved(ticket: SevaTicket) -> bool:
    return ticket.review_status == ReviewStatus.APPROVED.value


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
        shown = [t for t in tickets
                 if t.show_publicly and t.occasion and t.payment_status in _SETTLED and approved(t)]
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
            status="active", devotee_name=ticket.devotee_name,
            photo_url=ticket.photo_url if approved(ticket) else None,
            visible_until=visible_until(ticket.seva_date), **base,
        )


class BlessingReviewService:
    """Staff approve or reject what a devotee asked to show: their photo (held
    under a private S3 key until approved) and their public name + occasion.
    Approving publishes the photo to the public gallery prefix; rejecting
    deletes it and keeps the booking private - the seva and its blessing
    email are unaffected either way."""

    def __init__(self, db: Session, storage: StorageService):
        self.db = db
        self.storage = storage

    def pending(self) -> List[BlessingReviewOut]:
        tickets = (
            self.db.query(SevaTicket)
            .filter(SevaTicket.review_status == ReviewStatus.PENDING.value,
                    SevaTicket.status != TicketStatus.CANCELLED)
            .order_by(SevaTicket.seva_date.asc(), SevaTicket.created_at.asc())
            .limit(200)
            .all()
        )
        return [self._out(t) for t in tickets]

    def _out(self, ticket: SevaTicket) -> BlessingReviewOut:
        preview = ticket.photo_url
        if ticket.photo_key and self.storage.enabled:
            preview = self.storage.presigned_get(ticket.photo_key)
        return BlessingReviewOut(
            id=ticket.id, ticket_number=ticket.ticket_number, seva_name=ticket.seva_name,
            devotee_name=ticket.devotee_name, occasion=ticket.occasion, seva_date=ticket.seva_date,
            show_publicly=ticket.show_publicly, payment_status=ticket.payment_status.value,
            review_status=ticket.review_status, photo_preview_url=preview,
        )

    def review(self, ticket_id: UUID, approve: bool) -> SevaTicket:
        ticket = self.db.query(SevaTicket).filter(SevaTicket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        if ticket.review_status is None:
            raise HTTPException(status_code=400, detail="This booking has nothing to review")
        if approve:
            self._approve(ticket)
        else:
            self._reject(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def _approve(self, ticket: SevaTicket) -> None:
        if ticket.photo_key:
            if not self.storage.enabled:
                raise HTTPException(status_code=503, detail="Photo storage is not configured")
            try:
                ticket.photo_url = self.storage.publish(ticket.photo_key, PUBLIC_PHOTO_PREFIX)
            except ClientError as exc:
                if exc.response.get("Error", {}).get("Code") not in ("NoSuchKey", "404"):
                    logger.exception("Publishing blessing photo %s failed", ticket.photo_key)
                    raise HTTPException(status_code=503, detail="Could not publish the photo. Please try again.")
                ticket.photo_url = None  # never actually uploaded - approve the rest
            except BotoCoreError:
                logger.exception("Publishing blessing photo %s failed", ticket.photo_key)
                raise HTTPException(status_code=503, detail="Could not publish the photo. Please try again.")
            ticket.photo_key = None
        ticket.review_status = ReviewStatus.APPROVED.value

    def _reject(self, ticket: SevaTicket) -> None:
        keys = [ticket.photo_key, self.storage.key_from_public_url(ticket.photo_url or "")]
        for key in filter(None, keys) if self.storage.enabled else ():
            try:
                self.storage.delete(key)
            except Exception:  # best-effort: never let cleanup block a takedown
                # Already off the website either way (the row no longer points
                # at it); log so an orphaned public object can be cleaned up.
                logger.exception("Deleting rejected blessing photo %s failed", key)
        ticket.photo_key = None
        ticket.photo_url = None
        ticket.show_publicly = False
        ticket.review_status = ReviewStatus.REJECTED.value
