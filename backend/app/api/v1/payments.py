from fastapi import APIRouter, Depends

from app.schemas.payment import PaymentStatusOut
from app.services.razorpay_service import RazorpayService
from app.utils.dependencies import get_razorpay_service

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("/status", response_model=PaymentStatusOut)
def payment_status(razorpay: RazorpayService = Depends(get_razorpay_service)):
    """Public: whether online payment is set up (RAZORPAY_KEY_ID/SECRET are
    set). The public donation form and the seva booking form's "pay online"
    option check this first, so they show the real thing only once it's
    actually configured - not a form that would 503 on every attempt, and not
    a coming-soon page once it's live either.

    Reveals nothing sensitive - `enabled` is exactly what an attempt to pay
    online would tell you anyway (503 vs a real order)."""
    return PaymentStatusOut(enabled=razorpay.enabled)
