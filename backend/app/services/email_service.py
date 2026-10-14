import logging
from email.message import EmailMessage
from typing import List, Optional, Tuple

import boto3

from app.core.config import settings
from app.services.email_template import NO_REPLY_TEXT, TEMPLE_NAME, Tone, render_email

# (file name, PDF bytes) - every attachment the site sends is a PDF it generated
Attachment = Tuple[str, bytes]

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

    def notify_admin(self, subject: str, body: str, **style) -> bool:
        if not self.enabled:
            logger.info("Skipping admin notification (SES not configured): %s", subject)
            return False
        style.setdefault("tone", "admin")
        return self._send(self.admin_email, subject, body, render_email(subject, body, **style),
                          log_label="admin notification")

    def send(self, to_email: str, subject: str, body: str, *, heading: Optional[str] = None,
             code: Optional[str] = None, cta: Optional[Tuple[str, str]] = None, tone: Tone = "normal",
             image: Optional[str] = None, attachments: Optional[List[Attachment]] = None) -> bool:
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
        html = render_email(subject, body, heading=heading, code=code, cta=cta, tone=tone, image=image,
                            attachments=[name for name, _ in attachments or []])
        return self._send(to_email, subject, f"{body}\n\n{self._footer()}", html, log_label="email",
                          attachments=attachments)

    def _footer(self) -> str:
        return (
            "--\n"
            f"{NO_REPLY_TEXT}\n"
            "This is an automated message from svvdthorur.org. Privacy Policy: "
            f"{settings.FRONTEND_BASE_URL}/legal/privacy-policy"
        )

    @property
    def source(self) -> str:
        """The From header: the temple's name in front of a bare address, so inboxes
        show "Sri Varasidhi Vinayaka Swamy Temple" rather than a no-reply address."""
        addr = self.from_email or ""
        return addr if "<" in addr else f'"{TEMPLE_NAME}" <{addr}>'

    def _raw(self, to_email: str, subject: str, body: str, html: str, attachments: List[Attachment]) -> bytes:
        msg = EmailMessage()
        msg["Subject"], msg["From"], msg["To"] = subject, self.source, to_email
        msg.set_content(body)
        msg.add_alternative(html, subtype="html")
        for name, data in attachments:
            msg.add_attachment(data, maintype="application", subtype="pdf", filename=name)
        return msg.as_bytes()

    def _send(self, to_email: str, subject: str, body: str, html: str, log_label: str,
              attachments: Optional[List[Attachment]] = None) -> bool:
        try:
            client = boto3.client("ses", region_name=self.region)
            if attachments:
                try:
                    client.send_raw_email(Source=self.source, Destinations=[to_email],
                                          RawMessage={"Data": self._raw(to_email, subject, body, html, attachments)})
                    return True
                except Exception:
                    # e.g. the server's IAM role allows ses:SendEmail but not ses:SendRawEmail -
                    # the message itself matters more than the PDF, so send it without.
                    logger.warning("Sending %s with attachments failed; retrying without them: %s",
                                   log_label, subject, exc_info=True)
            client.send_email(
                Source=self.source,
                Destination={"ToAddresses": [to_email]},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {"Text": {"Data": body, "Charset": "UTF-8"},
                             "Html": {"Data": html, "Charset": "UTF-8"}},
                },
            )
            return True
        except Exception:
            logger.warning("Failed to send %s to %s: %s", log_label, to_email, subject, exc_info=True)
            return False
