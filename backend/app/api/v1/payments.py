from fastapi import APIRouter, Depends, Request

from app.schemas.payment import (
    RazorpayOrderRequest, RazorpayOrderResponse, RazorpayVerifyRequest, RazorpayVerifyResponse,
)
from app.services.razorpay_service import RazorpayService
from app.utils.rate_limiter import enforce, get_client_ip, payment_order_limiter

router = APIRouter(prefix="/payments/razorpay", tags=["Payments (Razorpay - scaffolding)"])


def get_razorpay_service() -> RazorpayService:
    return RazorpayService()


@router.post("/orders", response_model=RazorpayOrderResponse)
def create_order(
    payload: RazorpayOrderRequest,
    request: Request,
    service: RazorpayService = Depends(get_razorpay_service),
):
    """Create a Razorpay order for the client to open in Checkout.js.

    Scaffolding: returns 503 until RAZORPAY_KEY_ID/RAZORPAY_KEY_SECRET are
    configured. Not yet called from the donation or seva ticket booking UI -
    see RazorpayService's docstring for the intended flow once wired up.
    """
    enforce(payment_order_limiter, get_client_ip(request), "Too many payment attempts. Please try again later.")
    return service.create_order(payload.amount, payload.purpose)


@router.post("/verify", response_model=RazorpayVerifyResponse)
def verify_payment(
    payload: RazorpayVerifyRequest,
    service: RazorpayService = Depends(get_razorpay_service),
):
    """Verify a completed payment's signature. Scaffolding - the caller is
    still responsible for creating the actual donation/ticket record and its
    finance ledger entry once verified=true; that wiring doesn't exist yet."""
    verified = service.verify_payment_signature(
        payload.razorpay_order_id, payload.razorpay_payment_id, payload.razorpay_signature
    )
    return RazorpayVerifyResponse(verified=verified)
