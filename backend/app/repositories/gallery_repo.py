from typing import Optional

from app.models.gallery import Gallery
from app.repositories.base import BaseRepository


class GalleryRepository(BaseRepository):
    _ORDER = (Gallery.sort_order.asc(), Gallery.created_at.desc(), Gallery.id.desc())

    def query(self, active_only: bool = True, category: Optional[str] = None):
        query = self.db.query(Gallery)
        if active_only:
            query = query.filter(Gallery.is_active.is_(True))
        if category:
            query = query.filter(Gallery.category == category.upper())
        return query.order_by(*self._ORDER)

    def get_all(self, active_only: bool = True):
        return self.query(active_only).all()

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
        return self.db.query(Gallery).filter(Gallery.is_active.is_(True)).count()
