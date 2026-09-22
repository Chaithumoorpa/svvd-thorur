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

    def notify_admin(self, subject: str, body: str) -> None:
        if not self.enabled:
            return
        self._send(self.admin_email, subject, body, log_label="admin notification")

    def send(self, to_email: str, subject: str, body: str) -> None:
        """Best-effort mail to an arbitrary recipient (a devotee, a new admin user, ...).
        Silently a no-op if SES isn't configured - never blocks the action that triggered it."""
        if not self.can_send_to_users or not to_email:
            return
        self._send(to_email, subject, body, log_label="email")

    def _send(self, to_email: str, subject: str, body: str, log_label: str) -> None:
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
        except Exception:
            logger.warning("Failed to send %s: %s", log_label, subject, exc_info=True)
