"""The printed/PDF ticket template used to hardcode the temple's name and
location as a fixed string. It now reads both from the temple profile row,
so editing the temple profile (Admin > Temple) is reflected on printed
tickets without a code change - with the same values as a fallback if the
profile row is somehow missing."""
from datetime import date

from app.models.seva_ticket import PaymentStatus, SevaTicket, TicketSource, TicketStatus
from app.models.temple import Temple
from app.repositories.pooja_repo import PoojaRepository
from app.repositories.seva_ticket_repo import SevaTicketRepository
from app.services.seva_ticket_service import SevaTicketService


def _ticket(number: str, token: str) -> SevaTicket:
    return SevaTicket(
        ticket_number=number, seva_id=1, seva_name="Archana",
        devotee_name="Test Devotee", mobile_number="9999999999", seva_date=date.today(),
        payment_status=PaymentStatus.FREE, amount=0, status=TicketStatus.ACTIVE,
        source=TicketSource.ONLINE, qr_token=token,
    )


def test_ticket_html_uses_configured_temple_name(db):
    db.add(Temple(name="Test Configured Temple Name", village="Testville",
                  district="Test District", state="Test State"))
    db.commit()

    service = SevaTicketService(SevaTicketRepository(db), PoojaRepository(db))
    html_out = service.generate_ticket_html(_ticket("SVVD-2026-000001", "tok1"))

    assert "Test Configured Temple Name" in html_out
    assert "Testville, Test District, Test State" in html_out


def test_ticket_html_falls_back_when_no_temple_row(db):
    service = SevaTicketService(SevaTicketRepository(db), PoojaRepository(db))
    html_out = service.generate_ticket_html(_ticket("SVVD-2026-000002", "tok2"))

    assert "Sri Varasiddi Vinayaka Swamy Devasthanam" in html_out
    assert "Thorur, Andhra Pradesh" in html_out
