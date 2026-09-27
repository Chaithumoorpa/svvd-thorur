"""Occasion blessing emails, sent on the occasion's own date - an Abhishekam's
occasion_date, or a seva booking's seva_date - not the moment payment is
collected.

A booking whose date has already arrived when it's paid for (or booked, if the
seva is free) is greeted right away by the request that paid for it; every
other one is picked up on the day by the daily `app.cli.send_occasion_greetings`
cron job. Either way a greeting is only sent once - see _deliver.
"""
from datetime import date, datetime, timedelta
from typing import Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.abhishekam import (
    ABHISHEKAM_VISIBILITY_DAYS, Abhishekam, AbhishekamPaymentStatus, AbhishekamVisibility,
)
from app.models.seva_ticket import PaymentStatus, SevaTicket, TicketStatus
from app.services.email_service import EmailService

# A greeting may still go out up to this many days into the occasion - covering
# a missed cron run, or a fee collected a few days late - but never later: the
# Abhishekam page it links to is only up for ABHISHEKAM_VISIBILITY_DAYS.
GREETING_WINDOW_DAYS = ABHISHEKAM_VISIBILITY_DAYS

_SIGNATURE = "Thank you,\nSri Varasidhi Vinayaka Swamy Devasthanam, Thorur"


def _long_date(day: date) -> str:
    return f"{day.day} {day.strftime('%B %Y')}"


class OccasionGreetingService:
    def __init__(self, db: Session, email: EmailService | None = None):
        self.db = db
        self.email = email or EmailService()

    @staticmethod
    def _in_window(day: date, today: date) -> bool:
        return today - timedelta(days=GREETING_WINDOW_DAYS - 1) <= day <= today

    def abhishekam_due(self, row: Abhishekam, today: date) -> bool:
        return (
            row.payment_status == AbhishekamPaymentStatus.PAID
            and row.greeting_sent_at is None
            and self._in_window(row.occasion_date, today)
        )

    def seva_due(self, ticket: SevaTicket, today: date) -> bool:
        return (
            bool(ticket.occasion) and bool(ticket.email)
            and ticket.status != TicketStatus.CANCELLED
            and ticket.payment_status in (PaymentStatus.FREE, PaymentStatus.PAID)
            and ticket.greeting_sent_at is None
            and self._in_window(ticket.seva_date, today)
        )

    def send_abhishekam(self, row: Abhishekam) -> bool:
        public_page = (
            "It is also shown on the day's public blessings page:\n"
            f"{settings.FRONTEND_BASE_URL}/abhishekam/blessings/{row.occasion_date.isoformat()}\n\n"
            if row.visibility == AbhishekamVisibility.PUBLIC else ""
        )
        return self._deliver(
            Abhishekam, row, row.email,
            f"Blessings on your {row.occasion}",
            f"Dear {row.devotee_name},\n\n"
            f"On the occasion of your {row.occasion} ({_long_date(row.occasion_date)}), your Abhishekam is "
            "offered at Sri Varasidhi Vinayaka Swamy Devasthanam, and we send you and your family warm "
            "greetings and blessings.\n\n"
            f"Your blessing page is open for {ABHISHEKAM_VISIBILITY_DAYS} days:\n"
            f"{settings.FRONTEND_BASE_URL}/abhishekam/{row.id}\n\n"
            f"{public_page}{_SIGNATURE}",
        )

    def send_seva(self, ticket: SevaTicket) -> bool:
        return self._deliver(
            SevaTicket, ticket, ticket.email,
            f"Blessings on your {ticket.occasion}",
            f"Dear {ticket.devotee_name},\n\n"
            f"On the occasion of your {ticket.occasion}, Sri Varasidhi Vinayaka Swamy Devasthanam "
            "sends you and your family warm greetings and blessings.\n\n"
            f"Your {ticket.seva_name} seva (ticket {ticket.ticket_number}) on {_long_date(ticket.seva_date)} "
            "is offered with your intentions for this occasion.\n\n"
            f"{_SIGNATURE}",
        )

    def send_due(self, today: date) -> Tuple[int, int]:
        """Everything due as of `today` that hasn't been greeted yet - the cron
        job's whole run. Returns (abhishekams sent, seva tickets sent)."""
        earliest = today - timedelta(days=GREETING_WINDOW_DAYS - 1)
        abhishekams = (
            self.db.query(Abhishekam)
            .filter(
                Abhishekam.payment_status == AbhishekamPaymentStatus.PAID,
                Abhishekam.greeting_sent_at.is_(None),
                Abhishekam.occasion_date.between(earliest, today),
            )
            .all()
        )
        tickets = (
            self.db.query(SevaTicket)
            .filter(
                SevaTicket.occasion.isnot(None),
                SevaTicket.email.isnot(None),
                SevaTicket.status != TicketStatus.CANCELLED,
                SevaTicket.payment_status.in_((PaymentStatus.FREE, PaymentStatus.PAID)),
                SevaTicket.greeting_sent_at.is_(None),
                SevaTicket.seva_date.between(earliest, today),
            )
            .all()
        )
        return (
            sum(self.send_abhishekam(row) for row in abhishekams),
            sum(self.send_seva(ticket) for ticket in tickets),
        )

    def _deliver(self, model, row, to_email: str, subject: str, body: str) -> bool:
        """Claims the row (greeting_sent_at: NULL -> now) in its own UPDATE
        before sending, so the cron job and a same-day payment can never both
        send it; releases the claim if SES doesn't accept the mail, so the
        next cron run retries while still inside the window."""
        claimed = (
            self.db.query(model)
            .filter(model.id == row.id, model.greeting_sent_at.is_(None))
            .update({model.greeting_sent_at: datetime.now()}, synchronize_session=False)
        )
        self.db.commit()
        if not claimed:
            return False
        sent = self.email.send(to_email, subject, body)
        if not sent:
            self.db.query(model).filter(model.id == row.id).update(
                {model.greeting_sent_at: None}, synchronize_session=False,
            )
            self.db.commit()
        self.db.refresh(row)
        return sent
