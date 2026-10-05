import uuid

import boto3
from fastapi import HTTPException

from app.core.config import settings

_ALLOWED_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}
# Non-standard names some browsers/pickers report for ordinary JPEGs.
_CONTENT_TYPE_ALIASES = {"image/jpg": "image/jpeg", "image/pjpeg": "image/jpeg"}


class StorageService:
    """Issues presigned S3 POST uploads so the browser uploads directly to the
    bucket (no file traffic through the backend). Credentials come from boto3's
    default chain - an EC2 instance role in production, so no keys are stored here.
    """

    def __init__(self):
        self.bucket = settings.S3_BUCKET_NAME
        self.region = settings.AWS_REGION

    @property
    def enabled(self) -> bool:
        return bool(self.bucket)

    def _client(self):
        # boto3's default endpoint resolution for S3 points at the legacy
        # global s3.amazonaws.com host for some regions, which returns a 307
        # redirect to the real regional endpoint for any bucket outside
        # us-east-1. A browser doesn't reliably re-send a multipart POST body
        # through that redirect (works fine for a plain GET/PUT from a
        # script, which is why this only broke real uploads) - pinning the
        # regional endpoint here means a presigned URL is correct on the
        # first request, no redirect involved.
        return boto3.client(
            "s3", region_name=self.region, endpoint_url=f"https://s3.{self.region}.amazonaws.com"
        )

    def create_upload(self, content_type: str, key_prefix: str = "gallery") -> dict:
        if not self.enabled:
            raise HTTPException(status_code=503, detail="Photo uploads are not configured")

        content_type = _CONTENT_TYPE_ALIASES.get(content_type.lower(), content_type.lower())
        ext = _ALLOWED_CONTENT_TYPES.get(content_type)
        if ext is None:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image type '{content_type}'. Use JPEG, PNG, WEBP, or GIF.",
            )

        key = f"{key_prefix}/{uuid.uuid4().hex}.{ext}"
        max_bytes = settings.S3_MAX_UPLOAD_MB * 1024 * 1024

        client = self._client()
        presigned = client.generate_presigned_post(
            Bucket=self.bucket,
            Key=key,
            Fields={"Content-Type": content_type},
            Conditions=[
                {"Content-Type": content_type},
                ["content-length-range", 1, max_bytes],
            ],
            ExpiresIn=300,
        )

        public_url = f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"
        return {
            "upload_url": presigned["url"],
            "fields": presigned["fields"],
            "public_url": public_url,
            "key": key,
            "max_bytes": max_bytes,
        }

    def upload_private(self, data: bytes, key: str, content_type: str) -> str:
        """Server-side upload of generated documents (ticket/receipt PDFs) that
        must stay private - PII, unlike public gallery photos. No bucket policy
        grants public read outside the gallery/ prefix, so this key is only
        reachable with the instance's own credentials (e.g. a presigned GET
        generated on demand) or direct console/API access."""
        if not self.enabled:
            raise RuntimeError("S3 is not configured (S3_BUCKET_NAME unset)")
        client = self._client()
        client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        return key

    # ---- blessing photos: uploaded privately, published only after staff review ----
    def public_url(self, key: str) -> str:
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"

    def key_from_public_url(self, url: str) -> str | None:
        """The key of one of this bucket's own public objects, else None."""
        prefix = self.public_url("")
        return url[len(prefix):] if self.enabled and url.startswith(prefix) else None

    def presigned_get(self, key: str, expires_in: int = 900) -> str:
        """Short-lived link for staff to view a private object (a photo awaiting review)."""
        return self._client().generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=expires_in,
        )

    def publish(self, key: str, public_prefix: str) -> str:
        """Copies a private object under a public-read prefix (gallery/...), deletes
        the private copy and returns the new public URL."""
        client = self._client()
        public_key = f"{public_prefix}/{key.rsplit('/', 1)[-1]}"
        client.copy_object(Bucket=self.bucket, Key=public_key, CopySource={"Bucket": self.bucket, "Key": key})
        client.delete_object(Bucket=self.bucket, Key=key)
        return self.public_url(public_key)

    def delete(self, key: str) -> None:
        self._client().delete_object(Bucket=self.bucket, Key=key)
