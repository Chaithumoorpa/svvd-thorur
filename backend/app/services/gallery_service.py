from typing import Optional

from fastapi import HTTPException

from app.models.gallery import Gallery
from app.repositories.gallery_repo import GalleryRepository
from app.schemas.gallery import GalleryCreate, GalleryUpdate


class GalleryService:
    def __init__(self, gallery_repository: GalleryRepository):
        self.repo = gallery_repository

    def query(self, active_only: bool = True, category: Optional[str] = None):
        return self.repo.query(active_only, category)

    def list_gallery(self, active_only: bool = True):
        return self.repo.get_all(active_only=active_only)

    def get_gallery(self, gallery_id: int) -> Gallery:
        gallery = self.repo.get_by_id(gallery_id)
        if not gallery:
            raise HTTPException(status_code=404, detail="Gallery item not found")
        return gallery

    def create_gallery(self, data: GalleryCreate, user_id: int) -> Gallery:
        return self.repo.create(Gallery(**data.model_dump(), created_by=user_id))

    def update_gallery(self, gallery_id: int, data: GalleryUpdate) -> Gallery:
        gallery = self.get_gallery(gallery_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            if value is None and key in ("title", "image_url", "category", "is_active", "sort_order"):
                continue
            setattr(gallery, key, value)
        return self.repo.update(gallery)

    def delete_gallery(self, gallery_id: int) -> Gallery:
        return self.repo.delete(self.get_gallery(gallery_id))
