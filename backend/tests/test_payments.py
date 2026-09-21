"""Razorpay scaffolding - inert (503) until keys are configured, and rate limited."""


def test_order_and_verify_are_503_when_unconfigured(client):
    # conftest doesn't set RAZORPAY_KEY_ID/SECRET, so this mirrors production
    # before the feature is turned on - same pattern as S3/SES.
    order = client.post("/api/v1/payments/razorpay/orders", json={"amount": 100})
    assert order.status_code == 503

    verify = client.post("/api/v1/payments/razorpay/verify", json={
        "razorpay_order_id": "order_x", "razorpay_payment_id": "pay_x", "razorpay_signature": "sig_x",
    })
    assert verify.status_code == 503


def test_order_validation(client):
    for amount in (0, -5, 2_000_000):
        r = client.post("/api/v1/payments/razorpay/orders", json={"amount": amount})
        assert r.status_code == 422, amount


def test_order_endpoint_is_rate_limited(client):
    for _ in range(10):
        client.post("/api/v1/payments/razorpay/orders", json={"amount": 100})
    r = client.post("/api/v1/payments/razorpay/orders", json={"amount": 100})
    assert r.status_code == 429
