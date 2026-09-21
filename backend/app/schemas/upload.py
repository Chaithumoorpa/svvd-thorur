from typing import Dict

from pydantic import BaseModel


class UploadUrlRequest(BaseModel):
    content_type: str


class UploadUrlResponse(BaseModel):
    upload_url: str
    fields: Dict[str, str]
    public_url: str
    key: str
    max_bytes: int
