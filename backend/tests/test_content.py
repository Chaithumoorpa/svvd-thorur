"""Announcements, festivals, poojas, gallery, temple info, timings, members."""
from datetime import date, timedelta

from app.models.audit_log import AuditLog


# ------------------------------------------------------------------ announcements
def test_announcement_crud_ordering_and_pagination(client, staff, db):
    _, headers = staff
    ids = []
    for i in range(5):
        response = client.post("/api/v1/announcements/", headers=headers, json={"title": f"News {i}"})
        assert response.status_code == 201
        ids.append(response.json()["id"])

    # newest first, ties broken by id: order is fully deterministic
    listing = [a["id"] for a in client.get("/api/v1/announcements/").json()]
    assert listing == sorted(ids, reverse=True)
    assert listing == [a["id"] for a in client.get("/api/v1/announcements/").json()]

    page = client.get("/api/v1/announcements/admin/all?page=2&page_size=2", headers=headers)
    assert page.status_code == 200
    assert page.headers["X-Total-Count"] == "5"
    assert [a["id"] for a in page.json()] == sorted(ids, reverse=True)[2:4]

    update = client.put(f"/api/v1/announcements/{ids[0]}", headers=headers,
                        json={"title": "Edited", "is_active": False})
    assert update.status_code == 200 and update.json()["is_active"] is False
    assert ids[0] not in [a["id"] for a in client.get("/api/v1/announcements/").json()]

    assert client.delete(f"/api/v1/announcements/{ids[1]}", headers=headers).json()["is_active"] is False
    # soft delete: still visible to staff
    all_ids = [a["id"] for a in client.get("/api/v1/announcements/admin/all", headers=headers).json()]
    assert ids[1] in all_ids


def test_announcement_validation(client, staff):
    _, headers = staff
    assert client.post("/api/v1/announcements/", headers=headers, json={"title": "   "}).status_code == 422
    bad_window = {"title": "x", "start_date": "2026-05-10", "end_date": "2026-05-01"}
    assert client.post("/api/v1/announcements/", headers=headers, json=bad_window).status_code == 422
    assert client.put("/api/v1/announcements/999", headers=headers, json={"title": "x"}).status_code == 404


def test_mutations_are_audited(client, staff, db):
    _, headers = staff
    client.post("/api/v1/announcements/", headers=headers, json={"title": "Audited"})
    log = db.query(AuditLog).filter_by(entity_type="announcement", action="CREATE").one()
    assert log.actor_username == "staff" and "Audited" in log.summary


# --------------------------------------------------------------------- festivals
def test_festival_full_lifecycle(client, admin):
    _, headers = admin
    soon = (date.today() + timedelta(days=10)).isoformat()
    past = (date.today() - timedelta(days=10)).isoformat()
    a = client.post("/api/v1/festivals/", headers=headers, json={"name": "Vinayaka Chavithi", "festival_date": soon})
    b = client.post("/api/v1/festivals/", headers=headers, json={"name": "Old Utsavam", "festival_date": past})
    c = client.post("/api/v1/festivals/", headers=headers, json={"name": "Undated Event"})
    assert a.status_code == b.status_code == c.status_code == 201

    names = [f["name"] for f in client.get("/api/v1/festivals/").json()]
    assert names == ["Old Utsavam", "Vinayaka Chavithi", "Undated Event"]  # dated first, undated last
    upcoming = [f["name"] for f in client.get("/api/v1/festivals/?upcoming=true").json()]
    assert "Old Utsavam" not in upcoming and "Vinayaka Chavithi" in upcoming

    assert client.post("/api/v1/festivals/", headers=headers, json={"name": "Old Utsavam"}).status_code == 400
    updated = client.put(f"/api/v1/festivals/{a.json()['id']}", headers=headers,
                         json={"location": "Main hall", "end_date": soon})
    assert updated.json()["location"] == "Main hall"
    bad = client.put(f"/api/v1/festivals/{a.json()['id']}", headers=headers, json={"end_date": past})
    assert bad.status_code == 422

    assert client.delete(f"/api/v1/festivals/{b.json()['id']}", headers=headers).status_code == 200
    assert "Old Utsavam" not in [f["name"] for f in client.get("/api/v1/festivals/").json()]
    assert client.get(f"/api/v1/festivals/{b.json()['id']}").status_code == 404


# ----------------------------------------------------------------------- poojas
def test_pooja_money_is_decimal_and_delete_is_soft(client, admin):
    _, headers = admin
    created = client.post("/api/v1/poojas/", headers=headers, json={
        "name": "Sahasranama Archana", "is_paid": True, "suggested_amount": 101.5,
        "start_time": "07:00:00", "end_time": "08:00:00"})
    assert created.status_code == 201, created.text
    assert created.json()["suggested_amount"] == 101.5

    assert client.post("/api/v1/poojas/", headers=headers, json={"name": "Paid No Price", "is_paid": True}).status_code == 422
    assert client.post("/api/v1/poojas/", headers=headers, json={
        "name": "Bad Times", "start_time": "09:00:00", "end_time": "08:00:00"}).status_code == 422
    assert client.post("/api/v1/poojas/", headers=headers, json={"name": "Sahasranama Archana"}).status_code == 400

    pid = created.json()["id"]
    assert client.delete(f"/api/v1/poojas/{pid}", headers=headers).status_code == 200
    assert client.get("/api/v1/poojas/").json() == []
    assert client.get(f"/api/v1/poojas/{pid}").status_code == 404
    assert len(client.get("/api/v1/poojas/admin/all", headers=headers).json()) == 1


# ----------------------------------------------------------------------- gallery
def test_gallery_urls_are_safe_and_admin_sees_hidden(client, staff):
    _, headers = staff
    bad = client.post("/api/v1/gallery/", headers=headers, json={
        "title": "x", "image_url": "javascript:alert(1)", "category": "temple"})
    assert bad.status_code == 422
    ok = client.post("/api/v1/gallery/", headers=headers, json={
        "title": "Gopuram", "image_url": "https://example.com/a.jpg", "category": "temple"})
    assert ok.status_code == 201 and ok.json()["category"] == "TEMPLE"
    hidden = client.post("/api/v1/gallery/", headers=headers, json={
        "title": "Hidden", "image_url": "/images/h.jpg", "is_active": False})
    assert hidden.status_code == 201
    assert [g["title"] for g in client.get("/api/v1/gallery/").json()] == ["Gopuram"]
    assert client.get("/api/v1/gallery/").headers["X-Total-Count"] == "1"
    assert len(client.get("/api/v1/gallery/admin/all", headers=headers).json()) == 2


# ------------------------------------------------------------------ temple + timings
def test_temple_profile_and_timings(client, admin, staff):
    assert client.get("/api/v1/temple/").status_code == 404  # not set up yet
    _, headers = admin
    created = client.put("/api/v1/temple/", headers=headers, json={
        "name": "Sri Varasiddhi Vinayaka Swamy Temple", "village": "Thorur", "pincode": "506163",
        "map_url": "https://maps.example.com/x", "contact_email": "info@example.org"})
    assert created.status_code == 200
    public = client.get("/api/v1/temple/")
    assert public.status_code == 200 and public.json()["village"] == "Thorur"
    assert "max-age" in public.headers["Cache-Control"]

    assert client.put("/api/v1/temple/", headers=headers, json={"map_url": "javascript:x"}).status_code == 422
    assert client.put("/api/v1/temple/", headers=headers, json={"pincode": "abc"}).status_code == 422
    # clearing a field with "" stores NULL; the mandatory name cannot be blanked
    cleared = client.put("/api/v1/temple/", headers=headers, json={"tagline": "", "name": ""})
    assert cleared.json()["tagline"] is None and cleared.json()["name"].startswith("Sri Varasiddhi")

    _, staff_headers = staff
    assert client.put("/api/v1/temple/", headers=staff_headers, json={"tagline": "x"}).status_code == 403

    t1 = client.post("/api/v1/temple/timings", headers=headers, json={
        "label": "Evening", "start_time": "16:30:00", "end_time": "20:30:00", "sort_order": 2})
    t2 = client.post("/api/v1/temple/timings", headers=headers, json={
        "label": "Morning", "start_time": "06:00:00", "end_time": "12:30:00", "sort_order": 1})
    assert t1.status_code == t2.status_code == 201
    assert [t["label"] for t in client.get("/api/v1/temple/timings").json()] == ["Morning", "Evening"]
    assert client.post("/api/v1/temple/timings", headers=headers, json={
        "label": "Bad", "start_time": "10:00:00", "end_time": "09:00:00"}).status_code == 422

    tid = t1.json()["id"]
    assert client.put(f"/api/v1/temple/timings/{tid}", headers=headers, json={"is_active": False}).status_code == 200
    assert [t["label"] for t in client.get("/api/v1/temple/timings").json()] == ["Morning"]
    assert client.put(f"/api/v1/temple/timings/{tid}", headers=headers,
                      json={"start_time": "21:00:00"}).status_code == 422
    assert client.delete(f"/api/v1/temple/timings/{tid}", headers=headers).status_code == 200


# ----------------------------------------------------------------------- members
def test_members_directory(client, admin, trustee):
    _, headers = admin
    for name, order in [("Zed Person", 2), ("Amar Person", 2), ("First Person", 1)]:
        r = client.post("/api/v1/temple-members/", headers=headers, json={
            "name": name, "phone": "+91 98765 43210", "sort_order": order, "position": "Trustee"})
        assert r.status_code == 201, r.text
    assert client.post("/api/v1/temple-members/", headers=headers,
                       json={"name": "Bad", "phone": "abc"}).status_code == 422
    assert client.post("/api/v1/temple-members/", headers=headers,
                       json={"name": "Bad Mail", "phone": "9876543210", "email": "nope"}).status_code == 422

    _, trustee_headers = trustee
    listing = client.get("/api/v1/temple-members/", headers=trustee_headers)
    assert [m["name"] for m in listing.json()] == ["First Person", "Amar Person", "Zed Person"]
    assert listing.headers["X-Total-Count"] == "3"
    # trustees may read but not write
    assert client.post("/api/v1/temple-members/", headers=trustee_headers,
                       json={"name": "Nope Nope", "phone": "9876543210"}).status_code == 403

    member_id = listing.json()[0]["id"]
    assert client.put(f"/api/v1/temple-members/{member_id}", headers=headers,
                      json={"show_on_website": True}).json()["show_on_website"] is True
    deleted = client.delete(f"/api/v1/temple-members/{member_id}", headers=headers).json()
    assert deleted["is_active"] is False and deleted["show_on_website"] is False
    assert client.get("/api/v1/public/committee").json() == []
