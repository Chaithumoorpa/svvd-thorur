from fastapi import HTTPException

from app.models.announcement import Announcement
from app.repositories.announcement_repo import AnnouncementRepository
from app.schemas.announcement import AnnouncementCreate


class AnnouncementService:
    def __init__(self, announcement_repository: AnnouncementRepository):
        self.repo = announcement_repository

    # ---- public --------------------------------------------------------------------
    def list_published(self, limit=None):
        return self.repo.get_all_active(limit=limit)

    def get_published(self, announcement_id: int) -> Announcement:
        announcement = self.repo.get_published_by_id(announcement_id)
        if not announcement:
            raise HTTPException(status_code=404, detail="Announcement not found")
        return announcement

    # ---- admin ---------------------------------------------------------------------
    def query_all(self):
        return self.repo.query_all()

    def _get(self, announcement_id: int) -> Announcement:
        announcement = self.repo.get_by_id(announcement_id)
        if not announcement:
            raise HTTPException(status_code=404, detail="Announcement not found")
        return announcement

    def create_announcement(self, data: AnnouncementCreate, user_id: int | None = None) -> Announcement:
        return self.repo.create(Announcement(**data.model_dump(), created_by_id=user_id))

    def update_announcement(self, announcement_id: int, data: dict) -> Announcement:
        announcement = self._get(announcement_id)
        # the merged window must stay valid even when only one bound is edited
        start = data.get("start_date", announcement.start_date)
        end = data.get("end_date", announcement.end_date)
        if start and end and end < start:
            raise HTTPException(status_code=422, detail="End date cannot be before start date")
        return self.repo.update(announcement, data)

    def delete_announcement(self, announcement_id: int) -> Announcement:
        return self.repo.delete(self._get(announcement_id))
