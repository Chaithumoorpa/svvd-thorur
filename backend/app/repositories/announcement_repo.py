from datetime import date
from typing import Optional

from sqlalchemy import or_

from app.models.announcement import Announcement
from app.repositories.base import BaseRepository


class AnnouncementRepository(BaseRepository):
    """Newest first everywhere; `id` breaks ties so the order is fully deterministic."""

    _ORDER = (Announcement.created_at.desc(), Announcement.id.desc())

    def _published(self, today: date):
        """Active AND inside its optional start/end window."""
        return self.db.query(Announcement).filter(
            Announcement.is_active.is_(True),
            or_(Announcement.start_date.is_(None), Announcement.start_date <= today),
            or_(Announcement.end_date.is_(None), Announcement.end_date >= today),
        )

    def get_all_active(self, today: Optional[date] = None, limit: Optional[int] = None):
        query = self._published(today or date.today()).order_by(*self._ORDER)
        if limit:
            query = query.limit(limit)
        return query.all()

    def get_published_by_id(self, announcement_id: int, today: Optional[date] = None):
        return self._published(today or date.today()).filter(Announcement.id == announcement_id).first()

    def query_all(self):
        """Admin view: every announcement, including inactive/expired."""
        return self.db.query(Announcement).order_by(*self._ORDER)

    def get_all(self):
        return self.query_all().all()

    def get_by_id(self, announcement_id: int):
        return self.db.query(Announcement).filter(Announcement.id == announcement_id).first()

    def get_by_source_festival(self, festival_id: int):
        return self.db.query(Announcement).filter(Announcement.source_festival_id == festival_id).first()

    def create(self, announcement: Announcement):
        self.db.add(announcement)
        self.db.commit()
        self.db.refresh(announcement)
        return announcement

    def update(self, announcement: Announcement, data: dict):
        for key, value in data.items():
            setattr(announcement, key, value)
        self.db.commit()
        self.db.refresh(announcement)
        return announcement

    def delete(self, announcement: Announcement):
        """Soft delete: keeps the row for audit/history."""
        announcement.is_active = False
        self.db.commit()
        self.db.refresh(announcement)
        return announcement

    def count(self) -> int:
        return self._published(date.today()).count()
