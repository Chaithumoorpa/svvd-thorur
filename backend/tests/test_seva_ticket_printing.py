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

    assert "Sri Varasiddhi Vinayaka Swamy Devasthanam" in html_out
    assert "Thorur, Andhra Pradesh" in html_out


def test_ticket_html_includes_the_logo_watermark(db):
    """_get_logo_base64() looks for assets/logo.png relative to the process's
    working directory - /app in the deployed container (WORKDIR + Dockerfile's
    `COPY assets ./assets`), backend/ when tests run. Regression guard for that
    file/COPY line actually being present, since a missing logo silently
    renders no watermark at all rather than erroring."""
    service = SevaTicketService(SevaTicketRepository(db), PoojaRepository(db))
    html_out = service.generate_ticket_html(_ticket("SVVD-2026-000003", "tok3"))

    assert 'class="watermark"' in html_out
    assert 'class="logo-mark"' in html_out
    assert "data:image/png;base64," in html_out


def test_ticket_html_shows_mobile_and_booking_source(db):
    service = SevaTicketService(SevaTicketRepository(db), PoojaRepository(db))
    html_out = service.generate_ticket_html(_ticket("SVVD-2026-000004", "tok4"))

    assert "9999999999" in html_out
    assert "Online booking" in html_out
    assert "Email:" not in html_out  # no email on this ticket


def test_ticket_html_shows_email_when_present(db):
    ticket = _ticket("SVVD-2026-000005", "tok5")
    ticket.email = "devotee@example.com"
    ticket.source = TicketSource.COUNTER

    service = SevaTicketService(SevaTicketRepository(db), PoojaRepository(db))
    html_out = service.generate_ticket_html(ticket)

    assert "devotee@example.com" in html_out
    assert "Temple counter" in html_out


def test_ticket_html_shows_temple_phone_when_configured(db):
    db.add(Temple(name="Test Temple", contact_phone="+91 98765 43210"))
    db.commit()

    service = SevaTicketService(SevaTicketRepository(db), PoojaRepository(db))
    html_out = service.generate_ticket_html(_ticket("SVVD-2026-000006", "tok6"))

    assert "+91 98765 43210" in html_out
