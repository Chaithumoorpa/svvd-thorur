"""Razorpay Orders API: create an order, verify a completed payment's
signature, and (best-effort) refund one that can't be honoured after all.

Used by two flows - see app/api/v1/seva_tickets.py (paid seva booking) and
app/api/v1/donors.py (public donation) - both following the same order-then-
confirm shape:
  1. POST .../online-order validates the request server-side (OTP/turnstile,
     the seva or donation is actually payable, the amount comes from our own
     records - never the client) and creates a Razorpay order for it. The
     validated details are handed back as a signed `payment_token` (a JWT,
     see app.core.security.create_access_token) - not stored server-side -
     so the confirm step below is stateless and survives a restart.
  2. The client opens Razorpay's Checkout.js with the order_id + key_id.
  3. POST .../online-confirm decodes payment_token, verifies its order_id
     matches, verifies the payment signature, and only then creates the real
     donation/seva ticket record - reusing the same booking/donation
     validation as the free/offline paths, since time has passed and, e.g.,
     the seva's slots for that date may have filled in the meantime. If so,
     the payment is refunded and the devotee is told plainly, rather than
     the temple keeping money for a seva it can't deliver.
"""
import logging
import uuid

import razorpay
from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)


class RazorpayService:
    def __init__(self):
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET

    @property
    def enabled(self) -> bool:
        return bool(self.key_id and self.key_secret)

    def _client(self) -> razorpay.Client:
        return razorpay.Client(auth=(self.key_id, self.key_secret))

    def require_enabled(self) -> None:
        if not self.enabled:
            raise HTTPException(status_code=503, detail="Online payments are not configured")

    def create_order(self, amount_rupees, purpose: str | None = None) -> dict:
        self.require_enabled()
        amount_paise = int(round(float(amount_rupees) * 100))
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
        self.require_enabled()
        try:
            self._client().utility.verify_payment_signature({
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            })
            return True
        except razorpay.errors.SignatureVerificationError:
            return False

    def payment_method(self, payment_id: str) -> str | None:
        """Best-effort: the actual instrument used (upi/card/netbanking/wallet),
        for the finance ledger's notes. Never blocks - a lookup failure just
        means the notes say "online" without the detail."""
        try:
            return self._client().payment.fetch(payment_id).get("method")
        except Exception:
            logger.warning("Could not fetch Razorpay payment %s for its method", payment_id, exc_info=True)
            return None

    def refund_payment(self, payment_id: str, amount_paise: int, notes: dict | None = None) -> bool:
        """Best-effort full refund - used when a payment succeeds but the thing
        it was for (a seva's last slot, taken by someone else in the meantime)
        is no longer available. Never raises: the caller has already told the
        devotee their payment will be refunded, and that promise must stand
        whether or not this call itself succeeds - a failure here needs a
        human to action from the logs/Razorpay dashboard, not a 500."""
        if not self.enabled:
            return False
        try:
            self._client().payment.refund(payment_id, {"amount": amount_paise, "notes": notes or {}})
            return True
        except Exception:
            logger.error("Refunding Razorpay payment %s (%d paise) failed - needs manual action",
                        payment_id, amount_paise, exc_info=True)
            return False
