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


def _sent(ses_client):
    kw = ses_client.send_email.call_args.kwargs
    return kw["Source"], kw["Message"]["Body"]["Html"]["Data"]


def test_every_email_also_goes_out_as_branded_html(monkeypatch):
    _configured(monkeypatch)
    with patch("app.services.email_service.boto3.client") as mock_boto:
        ses_client = MagicMock()
        mock_boto.return_value = ses_client
        EmailService().send("devotee@example.com", "Booking confirmed",
                            "Dear Ravi,\n\nTicket number: SV-1001\nSeva: Abhishekam\nDate: 2026-10-20\n\nThank you,\nSVVD Thorur")
        source, html = _sent(ses_client)
    assert source == '"Sri Varasidhi Vinayaka Swamy Temple" <temple@example.com>'
    assert "/email/logo.png" in html and "Sri Varasidhi Vinayaka Swamy Temple" in html
    assert "Booking confirmed</h1>" in html
    # "Label: value" lines become a details table
    assert ">Ticket number</td>" in html and ">SV-1001</td>" in html
    assert "/legal/privacy-policy" in html


def test_code_button_alert_and_escaping():
    from app.services.email_template import render_email
    html = render_email("Reset", "Your sign-in code is: 482913\n\nReset it here: https://svvdthorur.org/reset?token=a&b=1\n\n"
                        "<script>alert(1)</script>",
                        code="482913", cta=("Reset password", "https://svvdthorur.org/reset?token=a&b=1"), tone="alert")
    assert "letter-spacing:6px" in html and ">482913</td>" in html
    assert ">Reset password</a>" in html and 'href="https://svvdthorur.org/reset?token=a&amp;b=1"' in html
    assert "SECURITY NOTICE" in html
    assert "<script>" not in html and "&lt;script&gt;" in html


def test_admin_notifications_are_labelled(monkeypatch):
    _configured(monkeypatch)
    with patch("app.services.email_service.boto3.client") as mock_boto:
        ses_client = MagicMock()
        mock_boto.return_value = ses_client
        EmailService().notify_admin("New donation", "Donor: Sita\nAmount: Rs. 1001")
        _, html = _sent(ses_client)
    assert "TEMPLE ADMIN NOTIFICATION" in html and ">Sita</td>" in html


def test_attachments_go_as_a_raw_mime_message_with_the_pdf(monkeypatch):
    import email
    _configured(monkeypatch)
    with patch("app.services.email_service.boto3.client") as mock_boto:
        ses_client = MagicMock()
        mock_boto.return_value = ses_client
        EmailService().send("devotee@example.com", "Booking confirmed", "Your ticket is attached.",
                            attachments=[("Ticket_SV-1.pdf", b"%PDF-1.4 test")])
        ses_client.send_email.assert_not_called()
        raw = ses_client.send_raw_email.call_args.kwargs["RawMessage"]["Data"]
    msg = email.message_from_bytes(raw)
    parts = {p.get_content_type(): p for p in msg.walk()}
    assert {"text/plain", "text/html", "application/pdf"} <= set(parts)
    assert parts["application/pdf"].get_filename() == "Ticket_SV-1.pdf"
    assert parts["application/pdf"].get_payload(decode=True) == b"%PDF-1.4 test"
    html = parts["text/html"].get_payload(decode=True).decode()
    assert "ATTACHED TO THIS EMAIL" in html and "Ticket_SV-1.pdf" in html
    assert "Please do not reply to this email" in html
    assert "do not reply" in parts["text/plain"].get_payload(decode=True).decode()
