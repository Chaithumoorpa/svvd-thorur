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

    def create_upload(self, content_type: str, key_prefix: str = "gallery") -> dict:
        if not self.enabled:
            raise HTTPException(status_code=503, detail="Photo uploads are not configured")

        ext = _ALLOWED_CONTENT_TYPES.get(content_type)
        if ext is None:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image type '{content_type}'. Use JPEG, PNG, WEBP, or GIF.",
            )

        key = f"{key_prefix}/{uuid.uuid4().hex}.{ext}"
        max_bytes = settings.S3_MAX_UPLOAD_MB * 1024 * 1024

        client = boto3.client("s3", region_name=self.region)
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
        client = boto3.client("s3", region_name=self.region)
        client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        return key
