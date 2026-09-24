"""AuditService fires a Super Admin alert email when one actor logs several
deletions in a short window - a compromised account, a mistake, or someone
deleting a lot without saying so. Exercised directly at the service layer
(not through an API endpoint) since the trigger lives inside record() and
fires no matter which endpoint's deletion caused it."""
from unittest.mock import MagicMock, patch

from app.services.audit_service import AuditService


def _actor_and_root(make_user):
    actor, _ = make_user("ADMIN", username="deleter")
    root, _ = make_user("SUPER_ADMIN", username="root", email="root@example.com")
    return actor, root


def test_alerts_super_admins_when_an_actor_crosses_the_threshold(db, make_user):
    actor, root = _actor_and_root(make_user)
    sent = MagicMock()
    audit = AuditService(db)

    with patch("app.services.email_service.EmailService.send", sent):
        for i in range(3):
            audit.record(actor, "DELETE", "seva_ticket", i, f"Deleted ticket {i}")

    sent.assert_called_once()
    to_email, subject, body = sent.call_args[0]
    assert to_email == "root@example.com"
    assert "Repeated deletions" in subject
    assert actor.username in body


def test_does_not_alert_again_past_the_threshold(db, make_user):
    actor, _root = _actor_and_root(make_user)
    sent = MagicMock()
    audit = AuditService(db)

    with patch("app.services.email_service.EmailService.send", sent):
        for i in range(6):
            audit.record(actor, "DELETE", "seva_ticket", i, f"Deleted ticket {i}")

    sent.assert_called_once()  # only once, right at the 3rd deletion - not again at 4/5/6


def test_no_alert_below_the_threshold(db, make_user):
    actor, _root = _actor_and_root(make_user)
    sent = MagicMock()
    audit = AuditService(db)

    with patch("app.services.email_service.EmailService.send", sent):
        for i in range(2):
            audit.record(actor, "DELETE", "seva_ticket", i, f"Deleted ticket {i}")

    sent.assert_not_called()


def test_non_delete_actions_do_not_count(db, make_user):
    actor, _root = _actor_and_root(make_user)
    sent = MagicMock()
    audit = AuditService(db)

    with patch("app.services.email_service.EmailService.send", sent):
        for i in range(5):
            audit.record(actor, "UPDATE", "seva_ticket", i, f"Updated ticket {i}")

    sent.assert_not_called()


def test_no_alert_when_no_super_admin_has_an_email(db, make_user):
    actor, _ = make_user("ADMIN", username="deleter2")
    make_user("SUPER_ADMIN", username="root2")  # no email set
    sent = MagicMock()
    audit = AuditService(db)

    with patch("app.services.email_service.EmailService.send", sent):
        for i in range(3):
            audit.record(actor, "DELETE", "seva_ticket", i, f"Deleted ticket {i}")

    sent.assert_not_called()
