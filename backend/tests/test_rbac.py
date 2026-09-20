"""Backend authorization: every protected route is checked against the role matrix."""
import pytest

from app.core.rbac import Permission, permissions_for

ROLES = ["SUPER_ADMIN", "ADMIN", "TRUSTEE", "STAFF", "GENERAL_USER"]


def test_permission_matrix():
    assert permissions_for(["SUPER_ADMIN"]) == set(Permission)
    assert Permission.USERS_MANAGE not in permissions_for(["ADMIN"])
    assert Permission.AUDIT_READ not in permissions_for(["ADMIN"])
    assert Permission.DONORS_READ in permissions_for(["TRUSTEE"])
    assert Permission.DONORS_WRITE not in permissions_for(["TRUSTEE"])
    assert Permission.CONTENT_WRITE in permissions_for(["STAFF"])
    assert Permission.FINANCE_READ not in permissions_for(["STAFF"])
    assert permissions_for(["GENERAL_USER"]) == set()
    assert permissions_for(["NOT_A_ROLE"]) == set()
    assert permissions_for(None) == set()


# (method, path, json) -> roles that must be ALLOWED (everyone else: 403, no token: 401)
PROTECTED = [
    ("GET", "/api/v1/temple-members/", None, {"SUPER_ADMIN", "ADMIN", "TRUSTEE"}),
    ("GET", "/api/v1/donors/", None, {"SUPER_ADMIN", "ADMIN", "TRUSTEE"}),
    ("GET", "/api/v1/donations/", None, {"SUPER_ADMIN", "ADMIN", "TRUSTEE"}),
    ("GET", "/api/v1/finance/summary", None, {"SUPER_ADMIN", "ADMIN", "TRUSTEE"}),
    ("GET", "/api/v1/finance/ledger", None, {"SUPER_ADMIN", "ADMIN", "TRUSTEE"}),
    ("GET", "/api/v1/contacts/", None, {"SUPER_ADMIN", "ADMIN", "STAFF"}),
    ("GET", "/api/v1/seva-tickets/", None, {"SUPER_ADMIN", "ADMIN", "STAFF"}),
    ("GET", "/api/v1/announcements/admin/all", None, {"SUPER_ADMIN", "ADMIN", "STAFF"}),
    ("GET", "/api/v1/gallery/admin/all", None, {"SUPER_ADMIN", "ADMIN", "STAFF"}),
    ("GET", "/api/v1/poojas/admin/all", None, {"SUPER_ADMIN", "ADMIN", "STAFF"}),
    ("GET", "/api/v1/festivals/admin/all", None, {"SUPER_ADMIN", "ADMIN", "STAFF"}),
    ("GET", "/api/v1/temple/timings/all", None, {"SUPER_ADMIN", "ADMIN"}),
    ("GET", "/api/v1/meta/stats", None, {"SUPER_ADMIN", "ADMIN", "TRUSTEE", "STAFF"}),
    ("GET", "/api/v1/meta/activity", None, {"SUPER_ADMIN"}),
    ("GET", "/api/v1/audit-logs/", None, {"SUPER_ADMIN"}),
    ("GET", "/api/v1/auth/admin/users", None, {"SUPER_ADMIN"}),
    ("POST", "/api/v1/announcements/", {"title": "x"}, {"SUPER_ADMIN", "ADMIN", "STAFF"}),
    ("POST", "/api/v1/temple-members/", {"name": "Ravi Kumar", "phone": "9876543210"}, {"SUPER_ADMIN", "ADMIN"}),
    ("POST", "/api/v1/donors/", {"name": "Sita Devi"}, {"SUPER_ADMIN", "ADMIN"}),
    ("POST", "/api/v1/finance/expense", {
        "category": "OTHER", "description": "Flowers", "amount": "10", "payment_mode": "CASH",
        "paid_to": "Vendor", "expense_date": "2026-01-01"}, {"SUPER_ADMIN", "ADMIN"}),
    ("POST", "/api/v1/auth/admin/users", {
        "username": "newuser", "password": "Password123", "roles": ["STAFF"]}, {"SUPER_ADMIN"}),
]


@pytest.mark.parametrize("method,path,body,allowed", PROTECTED)
def test_route_matrix(client, make_user, method, path, body, allowed):
    # no token -> 401
    assert client.request(method, path, json=body).status_code == 401

    for role in ROLES:
        _, headers = make_user(role, username=f"{role.lower()}_x")
        response = client.request(method, path, json=body, headers=headers)
        if role in allowed:
            assert response.status_code < 400, f"{role} should reach {method} {path}: {response.text}"
        else:
            assert response.status_code == 403, f"{role} must be denied {method} {path}"


def test_roles_come_from_database_not_token(client, db, make_user):
    """Demoting a user takes effect immediately, even with an old, still-valid token."""
    user, headers = make_user("ADMIN", username="soon_demoted")
    assert client.get("/api/v1/donors/", headers=headers).status_code == 200
    user.roles = ["GENERAL_USER"]
    db.commit()
    assert client.get("/api/v1/donors/", headers=headers).status_code == 403


def test_inactive_user_token_rejected(client, db, make_user):
    user, headers = make_user("ADMIN", username="to_disable")
    user.is_active = False
    db.commit()
    assert client.get("/api/v1/donors/", headers=headers).status_code == 401


def test_forged_and_garbage_tokens_rejected(client):
    assert client.get("/api/v1/donors/", headers={"Authorization": "Bearer nonsense"}).status_code == 401
    assert client.get("/api/v1/donors/", headers={"Authorization": "Basic abc"}).status_code == 401
