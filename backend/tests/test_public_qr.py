def test_qr_png_for_allowed_path(client):
    r = client.get("/api/v1/public/qr", params={"path": "/register"})
    assert r.status_code == 200 and r.headers["content-type"] == "image/png"
    assert r.content.startswith(b"\x89PNG")


def test_qr_rejects_arbitrary_path(client):
    assert client.get("/api/v1/public/qr", params={"path": "//evil.com"}).status_code == 400
    assert client.get("/api/v1/public/qr", params={"path": "/admin"}).status_code == 400
