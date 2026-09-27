"""The donation receipt PDF: system generated (no signature line), with the
logo and every detail on record, and the amount in Indian-style words."""
from decimal import Decimal
from io import BytesIO

import pytest
from pypdf import PdfReader

from app.services.donation_receipt_service import _money, amount_in_words


@pytest.mark.parametrize("amount, words", [
    (Decimal("700"), "Rupees Seven Hundred Only"),
    (Decimal("1116"), "Rupees One Thousand One Hundred Sixteen Only"),
    (Decimal("125001.50"), "Rupees One Lakh Twenty Five Thousand One and Fifty Paise Only"),
    (Decimal("10000000"), "Rupees One Crore Only"),
    (Decimal("0.05"), "Rupees Zero and Five Paise Only"),
])
def test_amount_in_words(amount, words):
    assert amount_in_words(amount) == words


def test_indian_digit_grouping():
    assert [_money(v) for v in (700, Decimal("125001.5"), 12345678)] == ["700.00", "1,25,001.50", "1,23,45,678.00"]


def test_receipt_pdf_has_every_detail_and_no_signature_line(client, admin):
    _, headers = admin
    donor = client.post("/api/v1/donors/", headers=headers, json={
        "name": "Lakshmi <b>Devi</b>", "phone": "9876543210", "email": "lakshmi@example.com",
        "address": "Station Road, Thorrur", "pan_number": "ABCDE1234F",
    }).json()
    donation = client.post("/api/v1/donations/", headers=headers, json={
        "donor_id": donor["id"], "amount": 2501, "donation_type": "annadanam",
        "purpose": "Annadanam on Vinayaka Chavithi", "payment_mode": "UPI",
    }).json()
    number = client.post(f"/api/v1/donations/{donation['id']}/receipt", headers=headers).json()["receipt_number"]
    pdf = client.get(f"/api/v1/donations/{donation['id']}/receipt", headers=headers).content

    reader = PdfReader(BytesIO(pdf))
    assert len(reader.pages) == 1
    text = " ".join(reader.pages[0].extract_text().split())
    for expected in (number, "DONATION RECEIPT", "Lakshmi <b>Devi</b>", "9876543210", "lakshmi@example.com",
                     "Station Road, Thorrur", "ABCDE1234F", "Annadanam on Vinayaka Chavithi", "UPI",
                     "Rs. 2,501.00", "Rupees Two Thousand Five Hundred One Only",
                     "computer-generated receipt and does not require a signature"):
        assert expected in text, expected
    assert "Authorized Signature" not in text
    assert reader.pages[0].images, "the temple logo is on the receipt"
