"""Gallery: public listing (active-only, paginated, category-filtered) plus
admin CRUD. Unlike donors/members, delete here is a hard delete - the item
is gone, not deactivated."""
from app.models.gallery import Gallery


def _create(client, headers, **extra):
    body = {"title": "Deepam", "image_url": "https://example.com/deepam.jpg", **extra}
    return client.post("/api/v1/gallery", headers=headers, json=body)


def test_create_requires_content_write_and_validates_url(client, admin, trustee):
    _, headers = admin
    assert client.post("/api/v1/gallery", headers=headers,
                       json={"title": "x", "image_url": "javascript:alert(1)"}).status_code == 422
    assert client.post("/api/v1/gallery", headers=headers, json={"title": "x"}).status_code == 422  # image_url required

    _, trustee_headers = trustee
    assert _create(client, trustee_headers).status_code == 403
    assert client.get("/api/v1/gallery", headers={}).status_code == 200  # public read needs no auth


def test_public_listing_is_active_only_and_paginated(client, admin):
    _, headers = admin
    for i in range(3):
        assert _create(client, headers, title=f"Photo {i}").status_code == 201
    hidden = _create(client, headers, title="Hidden", is_active=False).json()

    public = client.get("/api/v1/gallery")
    assert public.headers["X-Total-Count"] == "3"
    assert all(item["title"] != "Hidden" for item in public.json())

    admin_all = client.get("/api/v1/gallery/admin/all", headers=headers)
    assert admin_all.headers["X-Total-Count"] == "4"

    page1 = client.get("/api/v1/gallery?page=1&page_size=2").json()
    page2 = client.get("/api/v1/gallery?page=2&page_size=2").json()
    assert len(page1) == 2 and len(page2) == 1
    assert {i["id"] for i in page1} | {i["id"] for i in page2} == {
        i["id"] for i in client.get("/api/v1/gallery/admin/all", headers=headers).json() if i["id"] != hidden["id"]
    }


def test_category_filter(client, admin):
    _, headers = admin
    _create(client, headers, title="Temple shot", category="temple")
    _create(client, headers, title="Festival shot", category="festival")

    temple_only = client.get("/api/v1/gallery?category=temple").json()
    assert [i["title"] for i in temple_only] == ["Temple shot"]
    assert temple_only[0]["category"] == "TEMPLE"  # normalized upper-case


def test_update_and_delete_are_gated_and_hard_delete(client, db, admin, staff):
    _, headers = admin
    item = _create(client, headers).json()

    _, staff_headers = staff  # STAFF holds CONTENT_WRITE too
    updated = client.put(f"/api/v1/gallery/{item['id']}", headers=staff_headers,
                         json={"title": "Renamed"})
    assert updated.status_code == 200 and updated.json()["title"] == "Renamed"

    deleted = client.delete(f"/api/v1/gallery/{item['id']}", headers=headers)
    assert deleted.status_code == 200
    assert db.query(Gallery).filter(Gallery.id == item["id"]).first() is None  # hard delete, no soft-delete row left


def test_update_and_delete_404_on_missing_item(client, admin):
    _, headers = admin
    assert client.put("/api/v1/gallery/999999", headers=headers, json={"title": "x"}).status_code == 404
    assert client.delete("/api/v1/gallery/999999", headers=headers).status_code == 404


def test_upload_url_gated_and_503_without_s3(client, admin, trustee):
    _, headers = admin
    r = client.post("/api/v1/gallery/upload-url", headers=headers, json={"content_type": "image/jpeg"})
    assert r.status_code == 503  # S3 not configured in tests - confirms the route/permission wiring

    assert client.post("/api/v1/gallery/upload-url", json={"content_type": "image/jpeg"}).status_code == 401
    _, trustee_headers = trustee
    assert client.post("/api/v1/gallery/upload-url", headers=trustee_headers,
                       json={"content_type": "image/jpeg"}).status_code == 403


def test_upload_url_rejects_unsupported_content_type(client, admin, monkeypatch):
    """S3 disabled short-circuits before the content-type check - patch it
    enabled to reach the actual validation being tested here."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "S3_BUCKET_NAME", "fake-bucket")
    _, headers = admin
    r = client.post("/api/v1/gallery/upload-url", headers=headers, json={"content_type": "application/pdf"})
    assert r.status_code == 400
