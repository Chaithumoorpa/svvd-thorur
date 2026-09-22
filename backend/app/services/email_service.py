import logging

import boto3

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Best-effort admin notification emails via AWS SES. Credentials come
    from boto3's default chain (an EC2 instance role in production, matching
    StorageService) - never stored here. Every call swallows its own errors:
    a mail delivery hiccup must never block the actual contact/booking/
    donation action that triggered it."""

    def __init__(self):
        self.region = settings.AWS_REGION
        self.from_email = settings.SES_FROM_EMAIL
        self.admin_email = settings.ADMIN_NOTIFICATION_EMAIL

    @property
    def enabled(self) -> bool:
        return bool(self.from_email and self.admin_email)

    @property
    def can_send_to_users(self) -> bool:
        """SES sandbox mode only lets sending to verified addresses; once out of
        sandbox this is the same requirement (a verified from_email) as admin mail."""
        return bool(self.from_email)

    def notify_admin(self, subject: str, body: str) -> bool:
        if not self.enabled:
            logger.info("Skipping admin notification (SES not configured): %s", subject)
            return False
        return self._send(self.admin_email, subject, body, log_label="admin notification")

    def send(self, to_email: str, subject: str, body: str) -> bool:
        """Best-effort mail to an arbitrary recipient (a devotee, a new admin user, ...).
        A no-op (logged, not raised) if SES isn't configured or there's no recipient -
        never blocks the action that triggered it. Returns whether the mail was
        actually accepted by SES, for the rare caller (e.g. OTP request) where
        the user needs to know delivery failed rather than wait forever - most
        callers can and should ignore the return value, same as before."""
        if not self.can_send_to_users:
            logger.info("Skipping email (SES not configured): %s", subject)
            return False
        if not to_email:
            logger.info("Skipping email (no recipient address): %s", subject)
            return False
        return self._send(to_email, subject, body, log_label="email")

    def _send(self, to_email: str, subject: str, body: str, log_label: str) -> bool:
        try:
            client = boto3.client("ses", region_name=self.region)
            client.send_email(
                Source=self.from_email,
                Destination={"ToAddresses": [to_email]},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {"Text": {"Data": body, "Charset": "UTF-8"}},
                },
            )
            return True
        except Exception:
            logger.warning("Failed to send %s to %s: %s", log_label, to_email, subject, exc_info=True)
            return False
