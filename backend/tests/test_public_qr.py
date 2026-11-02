def test_qr_png_for_allowed_path(client):
    r = client.get("/api/v1/public/qr", params={"path": "/register"})
    assert r.status_code == 200 and r.headers["content-type"] == "image/png"
    assert r.content.startswith(b"\x89PNG")


def test_qr_rejects_arbitrary_path(client):
    assert client.get("/api/v1/public/qr", params={"path": "//evil.com"}).status_code == 400
    assert client.get("/api/v1/public/qr", params={"path": "/admin"}).status_code == 400


def test_tv_sections_default_all_and_saved_choice_round_trips(client, db, admin):
    _, admin_headers = admin
    from app.models.temple import Temple
    db.add(Temple(name="Test Temple")); db.commit()
    assert "timings" in client.get("/api/v1/temple/").json()["tv_sections"]  # NULL = everything
    r = client.put("/api/v1/temple/", json={"tv_sections": ["timings", "qr", "timings"]}, headers=admin_headers)
    assert r.status_code == 200 and r.json()["tv_sections"] == ["timings", "qr"]
    assert client.put("/api/v1/temple/", json={"tv_sections": ["finance"]}, headers=admin_headers).status_code == 422
