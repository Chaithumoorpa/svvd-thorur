from app.repositories.gallery_repo import GalleryRepository
from app.schemas.gallery import GalleryCreate, GalleryUpdate
from app.models.gallery import Gallery
from fastapi import HTTPException

class GalleryService:
    def __init__(self, gallery_repository: GalleryRepository):
        self.gallery_repository = gallery_repository

    def list_gallery(self, active_only: bool = True):
        return self.gallery_repository.get_all(active_only=active_only)

    def get_gallery(self, gallery_id: int):
        gallery = self.gallery_repository.get_by_id(gallery_id)
        if not gallery:
            raise HTTPException(status_code=404, detail="Gallery item not found")
        return gallery

    def create_gallery(self, data: GalleryCreate, user_id: int):
        gallery = Gallery(**data.dict(), created_by=user_id)
        return self.gallery_repository.create(gallery)

    def update_gallery(self, gallery_id: int, data: GalleryUpdate):
        gallery = self.get_gallery(gallery_id)
        
        for key, value in data.dict(exclude_unset=True).items():
            setattr(gallery, key, value)
            
        return self.gallery_repository.update(gallery)

    def delete_gallery(self, gallery_id: int):
        gallery = self.get_gallery(gallery_id)
        return self.gallery_repository.delete(gallery)
