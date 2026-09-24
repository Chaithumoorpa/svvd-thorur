"""POST /temple-members/upload-url - presigned S3 upload for a member's photo.
Gated by MEMBERS_WRITE, same as create/update/delete. S3 isn't configured in
tests (no S3_BUCKET_NAME), so a permitted caller gets the same 503
StorageService.create_upload raises for the gallery upload endpoint - this
confirms the permission gate and route wiring, not the S3 call itself."""


def _upload(client, headers):
    return client.post("/api/v1/temple-members/upload-url", headers=headers, json={"content_type": "image/jpeg"})


def test_admin_can_reach_the_upload_endpoint(client, admin):
    _, headers = admin
    r = _upload(client, headers)
    assert r.status_code == 503, r.text  # S3 not configured in tests


def test_trustee_cannot_upload_member_photos(client, trustee):
    _, headers = trustee
    assert _upload(client, headers).status_code == 403


def test_staff_cannot_upload_member_photos(client, staff):
    _, headers = staff
    assert _upload(client, headers).status_code == 403


def test_upload_requires_authentication(client):
    assert _upload(client, {}).status_code == 401
