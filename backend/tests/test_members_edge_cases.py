"""Temple member directory edge cases not covered by test_content.py's
happy-path CRUD: not-found, phone/email validation, and read-only access."""


def _create(client, headers, **extra):
    body = {"name": "Ravi Kumar", "phone": "9876543210", **extra}
    return client.post("/api/v1/temple-members/", headers=headers, json=body)


def test_get_update_delete_404_on_missing_member(client, admin):
    _, headers = admin
    assert client.get("/api/v1/temple-members/999999", headers=headers).status_code == 404
    assert client.put("/api/v1/temple-members/999999", headers=headers, json={"name": "Renamed"}).status_code == 404
    assert client.delete("/api/v1/temple-members/999999", headers=headers).status_code == 404


def test_phone_and_email_validation(client, admin):
    _, headers = admin
    assert _create(client, headers, phone="abc").status_code == 422
    assert _create(client, headers, phone="123").status_code == 422  # too few digits
    assert _create(client, headers, name="R").status_code == 422  # min_length=2
    assert _create(client, headers, email="not-an-email").status_code == 422


def test_trustee_can_read_but_not_write(client, admin, trustee):
    _, headers = admin
    member = _create(client, headers).json()

    _, trustee_headers = trustee
    assert client.get(f"/api/v1/temple-members/{member['id']}", headers=trustee_headers).status_code == 200
    assert client.put(f"/api/v1/temple-members/{member['id']}", headers=trustee_headers,
                      json={"name": "Blocked"}).status_code == 403
    assert client.delete(f"/api/v1/temple-members/{member['id']}", headers=trustee_headers).status_code == 403


def test_delete_is_a_soft_delete(client, admin):
    _, headers = admin
    member = _create(client, headers).json()
    deleted = client.delete(f"/api/v1/temple-members/{member['id']}", headers=headers)
    assert deleted.status_code == 200 and deleted.json()["is_active"] is False

    # the row still exists and is directly fetchable by id, just excluded from the active listing
    assert client.get(f"/api/v1/temple-members/{member['id']}", headers=headers).status_code == 200
    listing = client.get("/api/v1/temple-members/", headers=headers).json()
    assert all(m["id"] != member["id"] for m in listing)


def test_required_fields_cannot_be_blanked_via_update(client, admin):
    _, headers = admin
    member = _create(client, headers).json()
    unchanged = client.put(f"/api/v1/temple-members/{member['id']}", headers=headers,
                           json={"name": None, "phone": None}).json()
    assert unchanged["name"] == "Ravi Kumar" and unchanged["phone"] == "9876543210"
