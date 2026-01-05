from sqlalchemy.orm import Session
from app.models.announcement import Announcement
from app.repositories.base import BaseRepository


class AnnouncementRepository(BaseRepository):

    def get_all_active(self):
        """
        Get all active announcements ordered by creation date (newest first).
        This ensures stable ordering for frontend display and prevents UI misalignment.
        """
        return (
            self.db.query(Announcement)
            .filter(Announcement.is_active == True)
            .order_by(Announcement.created_at.desc())  # Newest announcements first
            .all()
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
