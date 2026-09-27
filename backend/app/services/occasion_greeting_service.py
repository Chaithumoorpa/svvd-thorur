"""Occasion blessing emails for seva bookings, sent on the seva date itself -
not the moment payment is collected.

A booking whose date has already arrived when it's paid for (or booked, if the
seva is free) is greeted right away by the request that paid for it; every
other one is picked up on the day by the daily `app.cli.send_occasion_greetings`
cron job. Either way a greeting is only sent once - see _deliver.
"""
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.seva_ticket import PaymentStatus, SevaTicket, TicketStatus
from app.services.blessing_service import BLESSING_VISIBLE_DAYS
from app.services.email_service import EmailService

# A greeting may still go out up to this many days into the occasion - covering
# a missed cron run, or a fee collected a few days late - but never later: the
# blessing page it links to is only up for BLESSING_VISIBLE_DAYS.
GREETING_WINDOW_DAYS = BLESSING_VISIBLE_DAYS


def _long_date(day: date) -> str:
    return f"{day.day} {day.strftime('%B %Y')}"


class OccasionGreetingService:
    def __init__(self, db: Session, email: EmailService | None = None):
        self.db = db
        self.email = email or EmailService()

    def seva_due(self, ticket: SevaTicket, today: date) -> bool:
        return (
            bool(ticket.occasion) and bool(ticket.email)
            and ticket.status != TicketStatus.CANCELLED
            and ticket.payment_status in (PaymentStatus.FREE, PaymentStatus.PAID)
            and ticket.greeting_sent_at is None
            and today - timedelta(days=GREETING_WINDOW_DAYS - 1) <= ticket.seva_date <= today
        )

    def send_seva(self, ticket: SevaTicket) -> bool:
        public_page = ""
        if ticket.show_publicly:
            public_page = (
                "As you chose, it is also shown on the day's public blessings page:\n"
                f"{settings.FRONTEND_BASE_URL}/abhishekam/blessings/{ticket.seva_date.isoformat()}\n\n"
            )
        return self._deliver(
            ticket, ticket.email,
            f"Blessings on your {ticket.occasion}",
            f"Dear {ticket.devotee_name},\n\n"
            f"On the occasion of your {ticket.occasion}, Sri Varasidhi Vinayaka Swamy Devasthanam "
            "sends you and your family warm greetings and blessings.\n\n"
            f"Your {ticket.seva_name} seva (ticket {ticket.ticket_number}) on {_long_date(ticket.seva_date)} "
            "is offered with your intentions for this occasion.\n\n"
            f"Your blessing page is open for {BLESSING_VISIBLE_DAYS} days:\n"
            f"{settings.FRONTEND_BASE_URL}/blessing/{ticket.id}\n\n"
            f"{public_page}"
            "Thank you,\nSri Varasidhi Vinayaka Swamy Devasthanam, Thorur",
        )

    def send_due(self, today: date) -> int:
        """Every seva booking due a greeting as of `today` - the cron job's
        whole run. Returns how many were sent."""
        earliest = today - timedelta(days=GREETING_WINDOW_DAYS - 1)
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
        return sum(self.send_seva(ticket) for ticket in tickets)

    def _deliver(self, ticket: SevaTicket, to_email: str, subject: str, body: str) -> bool:
        """Claims the ticket (greeting_sent_at: NULL -> now) in its own UPDATE
        before sending, so the cron job and a same-day payment can never both
        send it; releases the claim if SES doesn't accept the mail, so the next
        cron run retries while still inside the window."""
        claimed = (
            self.db.query(SevaTicket)
            .filter(SevaTicket.id == ticket.id, SevaTicket.greeting_sent_at.is_(None))
            .update({SevaTicket.greeting_sent_at: datetime.now()}, synchronize_session=False)
        )
        self.db.commit()
        if not claimed:
            return False
        sent = self.email.send(to_email, subject, body)
        if not sent:
            self.db.query(SevaTicket).filter(SevaTicket.id == ticket.id).update(
                {SevaTicket.greeting_sent_at: None}, synchronize_session=False,
            )
            self.db.commit()
        self.db.refresh(ticket)
        return sent
