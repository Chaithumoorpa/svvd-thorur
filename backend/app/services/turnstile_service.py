import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


class TurnstileService:
    """Verifies a Cloudflare Turnstile challenge token server-side before a
    sensitive public action (login, register, forgot-password) proceeds -
    a scripted attacker can't complete the widget, so this stops automated
    attempts even within the existing per-IP/per-account rate limits.

    A no-op (always passes) when TURNSTILE_SECRET_KEY isn't configured,
    matching how EmailService/StorageService degrade without their own keys -
    local dev and any environment that hasn't set up Turnstile yet still works.

    Once configured, a verification error (Cloudflare unreachable, timeout)
    is treated as a FAILED challenge, not a passed one - unlike email, where a
    delivery failure must never block the action, here the challenge IS the
    gate: failing open would mean an attacker gets through for free exactly
    when Cloudflare is having trouble. Rate limiting is already in place as a
    second line of defense, so this fails closed."""

    @property
    def enabled(self) -> bool:
        return bool(settings.TURNSTILE_SECRET_KEY)

    def verify(self, token: str | None, remote_ip: str | None = None) -> bool:
        if not self.enabled:
            return True
        if not token:
            return False
        try:
            data = {"secret": settings.TURNSTILE_SECRET_KEY, "response": token}
            if remote_ip:
                data["remoteip"] = remote_ip
            response = httpx.post(_VERIFY_URL, data=data, timeout=5)
            response.raise_for_status()
            return bool(response.json().get("success"))
        except Exception:
            logger.warning("Turnstile verification request failed", exc_info=True)
            return False
