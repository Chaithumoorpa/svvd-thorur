import uuid

import razorpay
from fastapi import HTTPException

from app.core.config import settings


class RazorpayService:
    """Order creation + payment verification via Razorpay's Orders API.

    Scaffolding: this is NOT yet wired into the donation or seva ticket
    booking flows. Once RAZORPAY_KEY_ID/RAZORPAY_KEY_SECRET are set (test-mode
    keys work fine to develop against), the intended flow is:
      1. Client calls POST /payments/razorpay/orders to get an order_id.
      2. Client opens Razorpay's Checkout.js with that order_id + key_id.
      3. On success, client calls POST /payments/razorpay/verify with the
         three values Razorpay's callback provides.
      4. Only once verified=true, create the actual donation/seva ticket
         record (and its finance ledger entry - see DonationService.create
         and SevaTicketService.create_counter_ticket for that pattern) with
         payment_mode reflecting the real method used, not hardcoded CASH.
    """

    def __init__(self):
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET

    @property
    def enabled(self) -> bool:
        return bool(self.key_id and self.key_secret)

    def _client(self) -> razorpay.Client:
        return razorpay.Client(auth=(self.key_id, self.key_secret))

    def create_order(self, amount_rupees: float, purpose: str | None = None) -> dict:
        if not self.enabled:
            raise HTTPException(status_code=503, detail="Online payments are not configured")

        amount_paise = int(round(amount_rupees * 100))
        try:
            order = self._client().order.create({
                "amount": amount_paise,
                "currency": "INR",
                "receipt": uuid.uuid4().hex[:32],
                "payment_capture": 1,
                "notes": {"purpose": purpose} if purpose else {},
            })
        except razorpay.errors.BadRequestError as exc:
            raise HTTPException(status_code=400, detail=f"Razorpay rejected the order: {exc}")

        return {
            "order_id": order["id"],
            "amount_paise": amount_paise,
            "currency": "INR",
            "key_id": self.key_id,
        }

    def verify_payment_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        if not self.enabled:
            raise HTTPException(status_code=503, detail="Online payments are not configured")
        try:
            self._client().utility.verify_payment_signature({
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            })
            return True
        except razorpay.errors.SignatureVerificationError:
            return False
