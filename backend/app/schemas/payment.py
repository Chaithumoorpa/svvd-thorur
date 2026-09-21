from typing import Optional

from pydantic import BaseModel, Field


class RazorpayOrderRequest(BaseModel):
    amount: float = Field(gt=0, le=1_000_000, description="Amount in rupees")
    purpose: Optional[str] = Field(default=None, max_length=200)


class RazorpayOrderResponse(BaseModel):
    order_id: str
    amount_paise: int
    currency: str
    key_id: str  # public key - safe to expose to the client, needed by Razorpay's Checkout.js


class RazorpayVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class RazorpayVerifyResponse(BaseModel):
    verified: bool
