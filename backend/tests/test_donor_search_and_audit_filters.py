"""Donor search (including LIKE-wildcard escaping and soft-delete exclusion),
donation filtering by donor/type, and the audit log's action/actor filters -
none of these query paths were exercised anywhere else."""


def _donor(client, headers, **extra):
    return client.post("/api/v1/donors/", headers=headers, json={"name": "Sita Devi", **extra}).json()


def test_donor_search_by_name_and_phone(client, admin):
    _, headers = admin
    _donor(client, headers, name="Ravi Kumar", phone="9876543210")
    _donor(client, headers, name="Geeta Rani", phone="9988776655")

    by_name = client.get("/api/v1/donors/?search=ravi", headers=headers).json()
    assert [d["name"] for d in by_name] == ["Ravi Kumar"]

    by_phone = client.get("/api/v1/donors/?search=998877", headers=headers).json()
    assert [d["name"] for d in by_phone] == ["Geeta Rani"]

    none = client.get("/api/v1/donors/?search=nomatch", headers=headers).json()
    assert none == []


def test_donor_search_escapes_like_wildcards(client, admin):
    """A literal '%' or '_' in the search term must not act as a SQL wildcard."""
    _, headers = admin
    _donor(client, headers, name="100% Devoted")
    _donor(client, headers, name="Anything Goes")

    exact = client.get("/api/v1/donors/?search=100%25 Devoted", headers=headers).json()
    assert [d["name"] for d in exact] == ["100% Devoted"]

    literal_percent_alone = client.get("/api/v1/donors/?search=%25", headers=headers).json()
    assert [d["name"] for d in literal_percent_alone] == ["100% Devoted"]  # not "everything"


def test_deleted_donor_excluded_from_search_and_listing(client, admin):
    _, headers = admin
    donor = _donor(client, headers, name="Soon Gone")
    client.delete(f"/api/v1/donors/{donor['id']}", headers=headers)

    assert client.get("/api/v1/donors/?search=Soon", headers=headers).json() == []
    listing = client.get("/api/v1/donors/", headers=headers).json()
    assert all(d["id"] != donor["id"] for d in listing)
    # the row itself still exists (soft delete) and is directly fetchable
    assert client.get(f"/api/v1/donors/{donor['id']}", headers=headers).status_code == 200


def test_donation_filters_by_donor_and_type(client, admin):
    _, headers = admin
    a = _donor(client, headers, name="Donor A")
    b = _donor(client, headers, name="Donor B")
    client.post("/api/v1/donations/", headers=headers,
               json={"donor_id": a["id"], "amount": 100, "donation_type": "general"})
    client.post("/api/v1/donations/", headers=headers,
               json={"donor_id": a["id"], "amount": 200, "donation_type": "annadanam"})
    client.post("/api/v1/donations/", headers=headers,
               json={"donor_id": b["id"], "amount": 300, "donation_type": "general"})

    for_a = client.get(f"/api/v1/donations/?donor_id={a['id']}", headers=headers).json()
    assert {d["amount"] for d in for_a} == {100, 200}

    general_only = client.get("/api/v1/donations/?donation_type=general", headers=headers).json()
    assert {d["amount"] for d in general_only} == {100, 300}


def test_audit_log_filters_by_action_and_actor(client, admin, super_admin):
    _, admin_headers = admin
    _, root_headers = super_admin
    _donor(client, admin_headers, name="Audited Donor")
    client.put(f"/api/v1/donors/{_donor(client, admin_headers, name='Second Donor')['id']}",
              headers=admin_headers, json={"phone": "9876543210"})

    creates = client.get("/api/v1/audit-logs/?action=CREATE", headers=root_headers).json()
    assert all(l["action"] == "CREATE" for l in creates) and len(creates) >= 2

    updates = client.get("/api/v1/audit-logs/?action=UPDATE", headers=root_headers).json()
    assert len(updates) == 1 and updates[0]["action"] == "UPDATE"

    by_actor = client.get("/api/v1/audit-logs/?actor=admin", headers=root_headers).json()
    assert all(l["actor_username"] == "admin" for l in by_actor)
    assert client.get("/api/v1/audit-logs/?actor=nobody", headers=root_headers).json() == []
