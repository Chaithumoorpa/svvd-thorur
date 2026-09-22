"""The printed/PDF ticket template used to hardcode the name of a different
temple ("Sri Varasiddi Vinayaka Swamy Devasthanam") - leftover boilerplate
never updated for this deployment. It now reads the real name from the
temple profile row."""
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
    db.add(Temple(name="Sri Vasavi Vishwakarma Devasthanam", village="Thorur",
                  district="Warangal", state="Telangana"))
    db.commit()

    service = SevaTicketService(SevaTicketRepository(db), PoojaRepository(db))
    html_out = service.generate_ticket_html(_ticket("SVVD-2026-000001", "tok1"))

    assert "Sri Vasavi Vishwakarma Devasthanam" in html_out
    assert "Varasiddi Vinayaka" not in html_out
    assert "Thorur, Warangal, Telangana" in html_out


def test_ticket_html_falls_back_when_no_temple_row(db):
    service = SevaTicketService(SevaTicketRepository(db), PoojaRepository(db))
    html_out = service.generate_ticket_html(_ticket("SVVD-2026-000002", "tok2"))

    assert "Sri Vasavi Vishwakarma Devasthanam" in html_out
