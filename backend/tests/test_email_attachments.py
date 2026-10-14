"""PDFs that go out with emails: the seva ticket (on booking and when the fee
is collected) and the donation receipt (when it's issued, once)."""
from tests.test_collect_payment import _pending_ticket


def _sends(sent, subject_start):
    return [c for c in sent.call_args_list if c.args[1].startswith(subject_start)]


def test_booking_and_payment_emails_carry_the_ticket_pdf(client, db, monkeypatch, staff):
    _, headers = staff
    ticket = _pending_ticket(client, db, monkeypatch)
    from app.services.email_service import EmailService
    sent = EmailService.send  # the MagicMock installed by _pending_ticket

    (booking,) = _sends(sent, "Booking confirmed")
    (name, pdf), = booking.kwargs["attachments"]
    assert name == f"Ticket_{ticket['ticket_number']}.pdf" and pdf.startswith(b"%PDF")

    client.post(f"/api/v1/seva-tickets/{ticket['id']}/collect-payment", headers=headers)
    (paid,) = _sends(sent, "Payment received")
    assert paid.args[0] == "devotee@example.com" and "Amount paid: Rs. 250" in paid.args[2]
    assert paid.kwargs["attachments"][0][1].startswith(b"%PDF")


def test_issuing_a_receipt_emails_it_to_the_donor_once(client, admin, monkeypatch):
    from unittest.mock import MagicMock
    sent = MagicMock(return_value=True)
    monkeypatch.setattr("app.services.email_service.EmailService.send", sent)
    _, headers = admin
    donor = client.post("/api/v1/donors/", headers=headers, json={"name": "Sita Devi", "email": "sita@example.com"}).json()
    donation = client.post("/api/v1/donations/", headers=headers, json={"donor_id": donor["id"], "amount": "1116"}).json()

    receipt = client.post(f"/api/v1/donations/{donation['id']}/receipt", headers=headers).json()["receipt_number"]
    client.post(f"/api/v1/donations/{donation['id']}/receipt", headers=headers)   # asking again doesn't re-send
    mails = _sends(sent, "Donation receipt")
    assert len(mails) == 1 and mails[0].args[0] == "sita@example.com"
    (name, pdf), = mails[0].kwargs["attachments"]
    assert name == f"Receipt_{receipt}.pdf" and pdf.startswith(b"%PDF")
