"""StorageService's blessing-photo helpers against a mocked boto3 client:
approval copies the private object to the public prefix and deletes the
private copy; only this bucket's own URLs map back to keys."""
from unittest.mock import MagicMock

from app.services.storage_service import StorageService


def _storage(monkeypatch):
    s = StorageService()
    s.bucket, s.region = "svvd", "ap-south-1"
    client = MagicMock()
    monkeypatch.setattr(s, "_client", lambda: client)
    return s, client


def test_publish_copies_to_the_public_prefix_then_deletes_the_private_copy(monkeypatch):
    s, client = _storage(monkeypatch)
    url = s.publish("blessings-pending/abc.jpg", "gallery/blessings")
    assert url == "https://svvd.s3.ap-south-1.amazonaws.com/gallery/blessings/abc.jpg"
    client.copy_object.assert_called_once_with(
        Bucket="svvd", Key="gallery/blessings/abc.jpg",
        CopySource={"Bucket": "svvd", "Key": "blessings-pending/abc.jpg"},
    )
    client.delete_object.assert_called_once_with(Bucket="svvd", Key="blessings-pending/abc.jpg")


def test_only_own_bucket_urls_map_back_to_keys(monkeypatch):
    s, _ = _storage(monkeypatch)
    assert s.key_from_public_url("https://svvd.s3.ap-south-1.amazonaws.com/gallery/blessings/a.jpg") == "gallery/blessings/a.jpg"
    assert s.key_from_public_url("https://evil.example.com/gallery/blessings/a.jpg") is None


def test_upload_url_is_for_the_private_prefix(monkeypatch, client):
    from app.main import app
    from app.utils.dependencies import get_storage_service
    s, boto = _storage(monkeypatch)
    boto.generate_presigned_post.return_value = {"url": "https://svvd.s3.ap-south-1.amazonaws.com/", "fields": {}}
    app.dependency_overrides[get_storage_service] = lambda: s
    try:
        r = client.post("/api/v1/seva-tickets/booking/upload-url", json={"content_type": "image/png"})
    finally:
        app.dependency_overrides.pop(get_storage_service, None)
    assert r.status_code == 200
    assert r.json()["key"].startswith("blessings-pending/")
    assert r.json()["public_url"] == ""
