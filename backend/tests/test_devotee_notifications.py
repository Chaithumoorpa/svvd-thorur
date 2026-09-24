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
