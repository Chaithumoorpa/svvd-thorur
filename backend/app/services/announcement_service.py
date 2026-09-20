from app.repositories.announcement_repo import AnnouncementRepository
from app.schemas.announcement import AnnouncementCreate
from app.models.announcement import Announcement

from fastapi import HTTPException


class AnnouncementService:
    def __init__(self, announcement_repository: AnnouncementRepository):
        self.announcement_repository = announcement_repository

    def list_active_announcements(self):
        """
        Returns all active announcements.
        Business rules can be added here later.
        """
        return self.announcement_repository.get_all_active()

    def list_all_announcements(self):
        """
        Returns all announcements.
        """
        return self.announcement_repository.get_all()

    def get_public_announcement(self, announcement_id: int):
        """Single announcement, only if visible to the public today."""
        return self.announcement_repository.get_visible_by_id(announcement_id)

    def get_announcement_details(self, announcement_id: int):
        """
        Returns a single announcement by id.
        """
        return self.announcement_repository.get_by_id(announcement_id)

    def create_announcement(self, data: AnnouncementCreate):
        announcement = Announcement(**data.dict())
        return self.announcement_repository.create(announcement)

    def update_announcement(self, announcement_id: int, data: dict):
        announcement = self.get_announcement_details(announcement_id)
        if not announcement:
            raise HTTPException(status_code=404, detail="Announcement not found")
        return self.announcement_repository.update(announcement, data)

    def delete_announcement(self, announcement_id: int):
        announcement = self.get_announcement_details(announcement_id)
        if not announcement:
            raise HTTPException(status_code=404, detail="Announcement not found")
        return self.announcement_repository.delete(announcement)
