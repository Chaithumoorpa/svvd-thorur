"""EmailService itself (not the callers that use it) - the privacy-policy
footer it appends to every user-facing email, and the sandbox/config gating
that decides whether it tries to send at all."""
from unittest.mock import MagicMock, patch

from app.services.email_service import EmailService


def _configured(monkeypatch):
    monkeypatch.setattr("app.services.email_service.settings.SES_FROM_EMAIL", "temple@example.com")
    monkeypatch.setattr("app.services.email_service.settings.ADMIN_NOTIFICATION_EMAIL", "admin@example.com")


def test_send_appends_the_privacy_policy_footer(monkeypatch):
    _configured(monkeypatch)
    with patch("app.services.email_service.boto3.client") as mock_boto:
        ses_client = MagicMock()
        mock_boto.return_value = ses_client

        ok = EmailService().send("devotee@example.com", "Booking confirmed", "Your ticket is ready.")

        assert ok is True
        body = ses_client.send_email.call_args.kwargs["Message"]["Body"]["Text"]["Data"]
        assert "Your ticket is ready." in body
        assert "/legal/privacy-policy" in body


def test_notify_admin_does_not_get_the_footer(monkeypatch):
    """Internal admin alerts aren't a devotee-facing message - no footer needed."""
    _configured(monkeypatch)
    with patch("app.services.email_service.boto3.client") as mock_boto:
        ses_client = MagicMock()
        mock_boto.return_value = ses_client

        EmailService().notify_admin("New booking", "Someone booked a seva.")

        body = ses_client.send_email.call_args.kwargs["Message"]["Body"]["Text"]["Data"]
        assert body == "Someone booked a seva."


def test_send_is_a_noop_without_from_email(monkeypatch):
    monkeypatch.setattr("app.services.email_service.settings.SES_FROM_EMAIL", None)
    with patch("app.services.email_service.boto3.client") as mock_boto:
        assert EmailService().send("devotee@example.com", "Subject", "Body") is False
        mock_boto.assert_not_called()
