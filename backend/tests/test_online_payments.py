"""Online payments (Razorpay), order-then-confirm: a paid seva booked and
paid for in one go, and a public donation - neither writes anything until
the payment is verified, and the seva path refunds a payment it can no
longer honour (the seva filled up between order and confirm)."""
import re
from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest

from app.api.v1.donors import get_donation_service, get_donor_service
from app.main import app
from app.models.pooja import Pooja
from app.models.seva_ticket import PaymentStatus, SevaTicket, TicketSource, TicketStatus
from app.repositories.donor_repo import DonorRepository
from app.services.donor_service import DonationService
from app.utils.dependencies import get_razorpay_service

TODAY = date.today()
SOON = TODAY + timedelta(days=10)


class FakeRazorpay:
    """A payment_id/signature of 'BAD' fails verification; everything else
    succeeds. Records every order/refund so a test can assert on them."""
    enabled = True

    def __init__(self):
        self.orders = []
        self.refunds = []

    def create_order(self, amount_rupees, purpose=None):
        order_id = f"order_{len(self.orders) + 1}"
        amount_paise = int(round(float(amount_rupees) * 100))
        self.orders.append({"order_id": order_id, "amount_paise": amount_paise, "purpose": purpose})
        return {"order_id": order_id, "amount_paise": amount_paise, "currency": "INR", "key_id": "rzp_test_fake"}

    def verify_payment_signature(self, order_id, payment_id, signature):
        return "BAD" not in (payment_id, signature)

    def payment_method(self, payment_id):
        return "upi"

    def refund_payment(self, payment_id, amount_paise, notes=None):
        self.refunds.append({"payment_id": payment_id, "amount_paise": amount_paise, "notes": notes})
        return True


@pytest.fixture()
def razorpay():
    fake = FakeRazorpay()
    app.dependency_overrides[get_razorpay_service] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_razorpay_service, None)


@pytest.fixture()
def sent(monkeypatch):
    mock = MagicMock(return_value=True)
    monkeypatch.setattr("app.services.email_service.EmailService.send", mock)
    monkeypatch.setattr("app.services.email_service.EmailService.notify_admin", mock)
    return mock


def _seva(db, cap=None, name="Abhishekam", amount=700):
    pooja = Pooja(name=name, pooja_type="daily", is_paid=True, suggested_amount=amount, daily_slot_cap=cap)
    db.add(pooja)
    db.commit()
    db.refresh(pooja)
    return pooja


def _ticket(db, seva, day, payment=PaymentStatus.PAID, status=TicketStatus.ACTIVE):
    ticket = SevaTicket(ticket_number=f"T-{seva.id}-{day}", seva_id=seva.id, seva_name=seva.name,
                        devotee_name="Existing Devotee", mobile_number="9000000000", seva_date=day,
                        payment_status=payment, amount=seva.suggested_amount, status=status,
                        qr_token=f"qr-{seva.id}-{day}", source=TicketSource.COUNTER)
    db.add(ticket)
    db.commit()
    return ticket


def _otp_token(client, sent, email="devotee@example.com"):
    client.post("/api/v1/seva-tickets/booking/request-otp", json={"email": email})
    code = next(re.search(r"\b(\d{6})\b", c.args[2]).group(1) for c in reversed(sent.call_args_list)
                if len(c.args) > 2 and re.search(r"\b(\d{6})\b", c.args[2]))
    return client.post("/api/v1/seva-tickets/booking/verify-otp",
                       json={"email": email, "code": code}).json()["booking_token"]


def _order_payload(seva, token, email="devotee@example.com", day=SOON, mobile="9876543210"):
    return {
        "seva_id": seva.id, "devotee_name": "Online Payer", "mobile_number": mobile,
        "seva_date": day.isoformat(), "email": email, "booking_token": token,
    }


# ------------------------------------------------------------------ payment status


def test_payment_status_reflects_configuration(client, razorpay):
    assert client.get("/api/v1/payments/status").json() == {"enabled": True}
    app.dependency_overrides.pop(get_razorpay_service, None)
    assert client.get("/api/v1/payments/status").json() == {"enabled": False}


# ------------------------------------------------------------------------- seva


def test_full_online_payment_books_a_paid_ticket(client, db, sent, razorpay):
    seva = _seva(db)
    token = _otp_token(client, sent)
    order = client.post("/api/v1/seva-tickets/booking/online-order",
                        json=_order_payload(seva, token)).json()
    assert order["amount_paise"] == 70000
    assert razorpay.orders[0]["amount_paise"] == 70000  # server-derived, not client-supplied

    confirm = client.post("/api/v1/seva-tickets/booking/online-confirm", json={
        "payment_token": order["payment_token"], "razorpay_order_id": order["order_id"],
        "razorpay_payment_id": "pay_1", "razorpay_signature": "sig_1",
    })
    assert confirm.status_code == 200, confirm.text
    ticket = confirm.json()
    assert (ticket["payment_status"], ticket["amount"], ticket["source"]) == ("PAID", 700.0, "ONLINE")

    from app.models.finance import IncomeTransaction, PaymentMode
    income = db.query(IncomeTransaction).filter(IncomeTransaction.reference_id == f"seva_ticket:{ticket['id']}").one()
    assert income.payment_mode == PaymentMode.ONLINE
    assert income.received_by is None
    assert "pay_1" in income.notes and "upi" in income.notes


def test_a_free_seva_has_nothing_to_pay_online(client, db, sent, razorpay):
    seva = _seva(db, amount=0)
    seva.is_paid = False
    db.commit()
    token = _otp_token(client, sent)
    r = client.post("/api/v1/seva-tickets/booking/online-order", json=_order_payload(seva, token))
    assert r.status_code == 400
    assert razorpay.orders == []  # never even asked Razorpay for an order


def test_order_amount_comes_from_the_seva_not_the_client(client, db, sent, razorpay):
    """The order endpoint's schema has no amount field at all - proven here by
    sending one and confirming it's simply ignored."""
    seva = _seva(db, amount=700)
    token = _otp_token(client, sent)
    payload = {**_order_payload(seva, token), "amount": 1}
    order = client.post("/api/v1/seva-tickets/booking/online-order", json=payload).json()
    assert order["amount_paise"] == 70000


def test_tampered_or_mismatched_payment_token_is_rejected(client, db, sent, razorpay):
    seva = _seva(db)
    token = _otp_token(client, sent)
    order = client.post("/api/v1/seva-tickets/booking/online-order",
                        json=_order_payload(seva, token)).json()

    wrong_order = client.post("/api/v1/seva-tickets/booking/online-confirm", json={
        "payment_token": order["payment_token"], "razorpay_order_id": "order_other",
        "razorpay_payment_id": "pay_1", "razorpay_signature": "sig_1",
    })
    assert wrong_order.status_code == 400

    garbage = client.post("/api/v1/seva-tickets/booking/online-confirm", json={
        "payment_token": "not-a-real-token", "razorpay_order_id": order["order_id"],
        "razorpay_payment_id": "pay_1", "razorpay_signature": "sig_1",
    })
    assert garbage.status_code == 400


def test_an_unverifiable_signature_books_nothing(client, db, sent, razorpay):
    seva = _seva(db)
    token = _otp_token(client, sent)
    order = client.post("/api/v1/seva-tickets/booking/online-order",
                        json=_order_payload(seva, token)).json()
    r = client.post("/api/v1/seva-tickets/booking/online-confirm", json={
        "payment_token": order["payment_token"], "razorpay_order_id": order["order_id"],
        "razorpay_payment_id": "BAD", "razorpay_signature": "BAD",
    })
    assert r.status_code == 400
    assert db.query(SevaTicket).filter(SevaTicket.mobile_number == "9876543210").count() == 0


def test_a_seva_that_fills_up_before_confirm_is_refunded(client, db, sent, razorpay):
    seva = _seva(db, cap=1)
    token = _otp_token(client, sent, email="payer@example.com")
    order = client.post("/api/v1/seva-tickets/booking/online-order",
                        json=_order_payload(seva, token, email="payer@example.com")).json()

    # Someone else takes the seva's only slot while payer is mid-checkout.
    _ticket(db, seva, SOON)

    r = client.post("/api/v1/seva-tickets/booking/online-confirm", json={
        "payment_token": order["payment_token"], "razorpay_order_id": order["order_id"],
        "razorpay_payment_id": "pay_2", "razorpay_signature": "sig_2",
    })
    assert r.status_code == 409
    assert "refund" in r.json()["detail"].lower()
    assert razorpay.refunds == [{"payment_id": "pay_2", "amount_paise": 70000,
                                 "notes": {"reason": "seva fully booked before confirmation"}}]
    assert db.query(SevaTicket).filter(SevaTicket.mobile_number == "9876543210").count() == 0


def test_online_order_endpoint_is_rate_limited(client, db, sent, razorpay):
    seva = _seva(db)
    token = _otp_token(client, sent)
    for _ in range(10):
        client.post("/api/v1/seva-tickets/booking/online-order", json=_order_payload(seva, token))
    r = client.post("/api/v1/seva-tickets/booking/online-order", json=_order_payload(seva, token))
    assert r.status_code == 429


# --------------------------------------------------------------------- donation


def test_full_public_donation_creates_donor_and_issues_a_receipt(client, db, sent, razorpay):
    order = client.post("/api/v1/donations/public/order", json={
        "donor_name": "Lakshmi Devi", "phone": "9876500001", "email": "lakshmi@example.com",
        "amount": 501, "donation_type": "general",
    }).json()
    assert order["amount_paise"] == 50100

    r = client.post("/api/v1/donations/public/confirm", json={
        "payment_token": order["payment_token"], "razorpay_order_id": order["order_id"],
        "razorpay_payment_id": "pay_d1", "razorpay_signature": "sig_d1",
    })
    assert r.status_code == 200, r.text
    donation = r.json()
    assert donation["amount"] == 501.0
    assert donation["payment_mode"] == "ONLINE"
    assert donation["receipt_number"]  # issued immediately - the money already arrived

    from app.models.donor import Donor
    donor = db.query(Donor).filter(Donor.phone == "9876500001").one()
    assert donor.name == "Lakshmi Devi" and donor.email == "lakshmi@example.com"


def test_a_repeat_donor_is_matched_by_phone_not_duplicated(client, db, sent, razorpay):
    from app.models.donor import Donor
    donor = Donor(name="Ravi Kumar", phone="9876500002")
    db.add(donor)
    db.commit()

    order = client.post("/api/v1/donations/public/order", json={
        "donor_name": "Ravi Kumar", "phone": "9876500002", "amount": 100,
    }).json()
    client.post("/api/v1/donations/public/confirm", json={
        "payment_token": order["payment_token"], "razorpay_order_id": order["order_id"],
        "razorpay_payment_id": "pay_d2", "razorpay_signature": "sig_d2",
    })
    assert db.query(Donor).filter(Donor.phone == "9876500002").count() == 1


def test_donation_amount_is_bounded(client, razorpay):
    for amount in (0, -5, 2_000_000):
        r = client.post("/api/v1/donations/public/order", json={
            "donor_name": "Test Donor", "phone": "9876500003", "amount": amount,
        })
        assert r.status_code == 422, amount


def test_donation_payment_endpoints_are_inert_when_razorpay_unconfigured(client):
    r = client.post("/api/v1/donations/public/order", json={
        "donor_name": "Test Donor", "phone": "9876500004", "amount": 100,
    })
    assert r.status_code == 503
