from datetime import date

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from app.models.announcement import Announcement
from app.repositories.base import BaseRepository


class AnnouncementRepository(BaseRepository):

    @staticmethod
    def _visible_now(today: date):
        """
        Public visibility rule: active AND inside the optional start/end window.
        The start_date/end_date columns existed but were never applied, so expired
        notices stayed on the site forever and future-dated ones showed early.
        """
        return and_(
            Announcement.is_active == True,
            or_(Announcement.start_date.is_(None), Announcement.start_date <= today),
            or_(Announcement.end_date.is_(None), Announcement.end_date >= today),
        )

    def get_all_active(self):
        """
        Get announcements that are publicly visible today, newest first.
        This ensures stable ordering for frontend display and prevents UI misalignment.
        """
        return (
            self.db.query(Announcement)
            .filter(self._visible_now(date.today()))
            .order_by(Announcement.created_at.desc())  # Newest announcements first
            .all()
        )

    def get_visible_by_id(self, announcement_id: int):
        """Single announcement, only if publicly visible today."""
        return (
            self.db.query(Announcement)
            .filter(Announcement.id == announcement_id, self._visible_now(date.today()))
            .first()
        )

    def get_all(self):
        """
        Get all announcements (admin view) ordered by creation date (newest first).
        """
        return (
            self.db.query(Announcement)
            .order_by(Announcement.created_at.desc())
            .all()
        )

    def get_by_id(self, announcement_id: int):
        return (
            self.db.query(Announcement)
            .filter(Announcement.id == announcement_id)
            .first()
        )

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
        announcement.is_active = False
        self.db.commit()
        return announcement

    def count(self) -> int:
        return self.db.query(Announcement).filter(Announcement.is_active == True).count()
