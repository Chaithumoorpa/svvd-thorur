"""Devotees get emailed when darshan timings change or a new announcement is
posted - never staff, trustees or admins. EmailService.send is mocked (SES
isn't configured in tests), so these assert who gets mailed, not delivery."""
from unittest.mock import MagicMock


def test_new_timing_notifies_devotees_not_staff(client, admin, make_user, monkeypatch):
    sent = MagicMock()
    monkeypatch.setattr("app.services.notification_service.EmailService.send", sent)
    _, headers = admin
    make_user("GENERAL_USER", username="devotee1", email="devotee1@example.com")
    make_user("GENERAL_USER", username="devotee2", email="devotee2@example.com")
    make_user("GENERAL_USER", username="no_email")  # no email on file - skipped
    make_user("STAFF", username="temple_staff", email="staff@example.com")

    r = client.post("/api/v1/temple/timings", headers=headers, json={
        "label": "Evening Aarti", "start_time": "18:00:00", "end_time": "19:00:00"})
    assert r.status_code == 201, r.text

    recipients = {call.args[0] for call in sent.call_args_list}
    assert recipients == {"devotee1@example.com", "devotee2@example.com"}


def test_updating_a_timing_notifies_devotees(client, admin, make_user, monkeypatch):
    sent = MagicMock()
    monkeypatch.setattr("app.services.notification_service.EmailService.send", sent)
    _, headers = admin
    make_user("GENERAL_USER", username="devotee3", email="devotee3@example.com")

    created = client.post("/api/v1/temple/timings", headers=headers, json={
        "label": "Morning", "start_time": "06:00:00", "end_time": "07:00:00"}).json()
    sent.reset_mock()

    r = client.put(f"/api/v1/temple/timings/{created['id']}", headers=headers, json={"start_time": "06:30:00"})
    assert r.status_code == 200
    sent.assert_called_once()
    assert sent.call_args[0][0] == "devotee3@example.com"


def test_deleting_a_timing_notifies_devotees(client, admin, make_user, monkeypatch):
    sent = MagicMock()
    monkeypatch.setattr("app.services.notification_service.EmailService.send", sent)
    _, headers = admin
    make_user("GENERAL_USER", username="devotee4", email="devotee4@example.com")

    created = client.post("/api/v1/temple/timings", headers=headers, json={
        "label": "Noon", "start_time": "12:00:00", "end_time": "13:00:00"}).json()
    sent.reset_mock()

    r = client.delete(f"/api/v1/temple/timings/{created['id']}", headers=headers)
    assert r.status_code == 200
    sent.assert_called_once()


def test_new_announcement_notifies_devotees_not_admins(client, staff, admin, make_user, monkeypatch):
    sent = MagicMock()
    monkeypatch.setattr("app.services.notification_service.EmailService.send", sent)
    _, headers = staff
    make_user("GENERAL_USER", username="devotee5", email="devotee5@example.com")
    make_user("ADMIN", username="another_admin", email="admin2@example.com")
    make_user("TRUSTEE", username="a_trustee", email="trustee1@example.com")

    r = client.post("/api/v1/announcements", headers=headers, json={"title": "Pooja on Friday"})
    assert r.status_code == 201, r.text

    recipients = {call.args[0] for call in sent.call_args_list}
    assert recipients == {"devotee5@example.com"}


def test_updating_an_announcement_does_not_notify(client, staff, make_user, monkeypatch):
    sent = MagicMock()
    monkeypatch.setattr("app.services.notification_service.EmailService.send", sent)
    _, headers = staff
    make_user("GENERAL_USER", username="devotee6", email="devotee6@example.com")

    created = client.post("/api/v1/announcements", headers=headers, json={"title": "Draft"}).json()
    sent.reset_mock()

    r = client.put(f"/api/v1/announcements/{created['id']}", headers=headers, json={"title": "Draft v2"})
    assert r.status_code == 200
    sent.assert_not_called()


def test_opted_out_devotee_is_skipped(client, staff, make_user, monkeypatch):
    sent = MagicMock()
    monkeypatch.setattr("app.services.notification_service.EmailService.send", sent)
    _, headers = staff
    make_user("GENERAL_USER", username="devotee7", email="devotee7@example.com")
    make_user("GENERAL_USER", username="devotee8", email="devotee8@example.com", receive_notifications=False)

    r = client.post("/api/v1/announcements", headers=headers, json={"title": "Rathotsavam"})
    assert r.status_code == 201, r.text

    recipients = {call.args[0] for call in sent.call_args_list}
    assert recipients == {"devotee7@example.com"}


def test_broadcast_email_includes_a_working_unsubscribe_link(client, staff, make_user, monkeypatch):
    sent = MagicMock()
    monkeypatch.setattr("app.services.notification_service.EmailService.send", sent)
    _, headers = staff
    make_user("GENERAL_USER", username="devotee9", email="devotee9@example.com")

    r = client.post("/api/v1/announcements", headers=headers, json={"title": "Vinayaka Chavithi"})
    assert r.status_code == 201, r.text

    body = sent.call_args[0][2]
    assert "/unsubscribe?token=" in body
    token = body.split("/unsubscribe?token=")[1].strip()

    check = client.get("/api/v1/auth/notification-preference", params={"token": token})
    assert check.status_code == 200
    assert check.json() == {"email": "devotee9@example.com", "receive_notifications": True}

    off = client.post("/api/v1/auth/notification-preference", json={"token": token, "receive_notifications": False})
    assert off.status_code == 200
    assert off.json()["receive_notifications"] is False

    # and it doubles as a resubscribe link
    on = client.post("/api/v1/auth/notification-preference", json={"token": token, "receive_notifications": True})
    assert on.json()["receive_notifications"] is True


def test_notification_preference_rejects_a_bad_token(client):
    r = client.get("/api/v1/auth/notification-preference", params={"token": "not-a-real-token"})
    assert r.status_code == 400
