from sqlalchemy.orm import Session
from app.models.gallery import Gallery
from app.repositories.base import BaseRepository

class GalleryRepository(BaseRepository):
    def get_all(self, active_only: bool = True):
        query = self.db.query(Gallery)
        if active_only:
            query = query.filter(Gallery.is_active == True)
        return query.all()

    def get_by_id(self, gallery_id: int):
        return self.db.query(Gallery).filter(Gallery.id == gallery_id).first()

    def create(self, gallery: Gallery):
        self.db.add(gallery)
        self.db.commit()
        self.db.refresh(gallery)
        return gallery

    def update(self, gallery: Gallery):
        self.db.add(gallery)
        self.db.commit()
        self.db.refresh(gallery)
        return gallery

    def delete(self, gallery: Gallery):
        self.db.delete(gallery)
        self.db.commit()
        return gallery

    def count(self) -> int:
        return self.db.query(Gallery).filter(Gallery.is_active == True).count()
