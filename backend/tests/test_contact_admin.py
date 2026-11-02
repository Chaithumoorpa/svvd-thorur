"""Contact message admin endpoints - get/update/delete, and the not-found
edge cases that never get exercised by the auto-reply-email tests in
test_notifications.py."""


def _submit(client, **extra):
    body = {"name": "Devotee", "email": "devotee@example.com", "subject": "Timing query",
            "message": "When is the evening pooja?", **extra}
    return client.post("/api/v1/contacts", json=body)


def test_get_message_requires_permission_and_404s(client, admin, trustee):
    _, headers = admin
    msg_id = _submit(client).json()["id"]

    assert client.get(f"/api/v1/contacts/{msg_id}", headers={}).status_code == 401
    _, trustee_headers = trustee
    assert client.get(f"/api/v1/contacts/{msg_id}", headers=trustee_headers).status_code == 403

    ok = client.get(f"/api/v1/contacts/{msg_id}", headers=headers)
    assert ok.status_code == 200 and ok.json()["subject"] == "Timing query"

    assert client.get("/api/v1/contacts/999999", headers=headers).status_code == 404


def test_update_and_delete_404_on_missing_message(client, admin):
    _, headers = admin
    assert client.patch("/api/v1/contacts/999999", headers=headers, json={"status": "RESOLVED"}).status_code == 404
    assert client.delete("/api/v1/contacts/999999", headers=headers).status_code == 404


def test_delete_removes_the_message(client, admin):
    _, headers = admin
    msg_id = _submit(client).json()["id"]
    assert client.delete(f"/api/v1/contacts/{msg_id}", headers=headers).status_code == 200
    assert client.get(f"/api/v1/contacts/{msg_id}", headers=headers).status_code == 404


def test_update_rejects_bad_status_enum(client, admin):
    _, headers = admin
    msg_id = _submit(client).json()["id"]
    assert client.patch(f"/api/v1/contacts/{msg_id}", headers=headers,
                        json={"status": "NOT_A_STATUS"}).status_code == 422


def test_submit_validates_required_fields_and_lengths(client):
    assert _submit(client, name="A").status_code == 422  # too short
    assert _submit(client, email="not-an-email").status_code == 422
    assert _submit(client, subject="ab").status_code == 422  # min_length=3
    assert _submit(client, message="hi").status_code == 422  # min_length=5


def test_honeypot_silently_drops_without_storing(client, admin):
    _, headers = admin
    r = _submit(client, website="http://spam.example")
    assert r.status_code == 201 and r.json()["id"] == 0
    listing = client.get("/api/v1/contacts/", headers=headers).json()
    assert listing == []  # nothing was actually stored


def test_pagination_and_status_filter(client, admin):
    _, headers = admin
    for i in range(3):
        _submit(client, subject=f"Query {i}")
    ids = [m["id"] for m in client.get("/api/v1/contacts/", headers=headers).json()]
    client.patch(f"/api/v1/contacts/{ids[0]}", headers=headers, json={"status": "RESOLVED"})

    pending = client.get("/api/v1/contacts/?status=PENDING", headers=headers).json()
    assert len(pending) == 2
    resolved = client.get("/api/v1/contacts/?status=RESOLVED", headers=headers).json()
    assert len(resolved) == 1

    page1 = client.get("/api/v1/contacts/?page=1&page_size=2", headers=headers)
    assert page1.headers["X-Total-Count"] == "3" and len(page1.json()) == 2
