"""Transactional emails triggered by admin actions (not the best-effort admin
alerts in test_* files elsewhere): contact resolution, new user welcome,
admin-initiated password resets. EmailService.send is mocked directly since
SES isn't configured in tests - these assert it's *called* with sane
arguments, not that mail is actually delivered."""
from unittest.mock import MagicMock


def _create_contact(client):
    return client.post("/api/v1/contacts", json={
        "name": "Dev A", "email": "dev@example.com",
        "subject": "Timing query", "message": "When is the evening pooja?",
    })


def test_contact_resolved_emails_the_submitter(client, super_admin, monkeypatch):
    sent = MagicMock()
    monkeypatch.setattr("app.api.v1.contact.EmailService.send", sent)
    _, headers = super_admin

    created = _create_contact(client)
    assert created.status_code == 201
    msg_id = created.json()["id"]
    sent.assert_not_called()

    resolved = client.patch(f"/api/v1/contacts/{msg_id}", headers=headers, json={"status": "RESOLVED"})
    assert resolved.status_code == 200
    sent.assert_called_once()
    to_email, subject, _body = sent.call_args[0]
    assert to_email == "dev@example.com"
    assert "Timing query" in subject


def test_resolving_again_does_not_resend(client, super_admin, monkeypatch):
    sent = MagicMock()
    monkeypatch.setattr("app.api.v1.contact.EmailService.send", sent)
    _, headers = super_admin

    msg_id = _create_contact(client).json()["id"]
    client.patch(f"/api/v1/contacts/{msg_id}", headers=headers, json={"status": "RESOLVED"})
    client.patch(f"/api/v1/contacts/{msg_id}", headers=headers, json={"admin_notes": "still resolved"})
    sent.assert_called_once()


def test_non_resolved_status_change_does_not_email(client, super_admin, monkeypatch):
    sent = MagicMock()
    monkeypatch.setattr("app.api.v1.contact.EmailService.send", sent)
    _, headers = super_admin

    msg_id = _create_contact(client).json()["id"]
    client.patch(f"/api/v1/contacts/{msg_id}", headers=headers, json={"status": "IN_PROGRESS"})
    sent.assert_not_called()


def test_new_user_creation_emails_credentials(client, super_admin, monkeypatch):
    sent = MagicMock()
    monkeypatch.setattr("app.api.v1.auth.EmailService.send", sent)
    _, headers = super_admin

    r = client.post("/api/v1/auth/admin/users", headers=headers, json={
        "username": "priest2", "password": "Temp12345", "roles": ["STAFF"], "email": "priest2@example.com",
    })
    assert r.status_code == 201
    sent.assert_called_once()
    to_email, _subject, body = sent.call_args[0]
    assert to_email == "priest2@example.com"
    assert "Temp12345" in body


def test_new_user_without_email_sends_nothing(client, super_admin, monkeypatch):
    sent = MagicMock()
    monkeypatch.setattr("app.api.v1.auth.EmailService.send", sent)
    _, headers = super_admin

    r = client.post("/api/v1/auth/admin/users", headers=headers,
                    json={"username": "priest3", "password": "Temp12345", "roles": ["STAFF"]})
    assert r.status_code == 201
    sent.assert_not_called()


def test_admin_password_reset_emails_new_password(client, super_admin, make_user, monkeypatch):
    sent = MagicMock()
    monkeypatch.setattr("app.api.v1.auth.EmailService.send", sent)
    _, headers = super_admin
    target, _ = make_user("STAFF", username="henry", email="henry@example.com")

    r = client.patch(f"/api/v1/auth/admin/users/{target.id}", headers=headers, json={"password": "Reset98765"})
    assert r.status_code == 200
    sent.assert_called_once()
    to_email, _subject, body = sent.call_args[0]
    assert to_email == "henry@example.com"
    assert "Reset98765" in body
