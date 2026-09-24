from datetime import date, timedelta
from typing import List, Optional

from app.models.announcement import Announcement
from app.models.festival import Festival
from app.repositories.announcement_repo import AnnouncementRepository
from app.repositories.festival_repo import FestivalRepository


class FestivalAnnouncementService:
    """Auto-creates one Announcement per festival that's due to be announced,
    `announce_days_before` days ahead of its date (see app/cli/generate_festival_
    announcements.py, meant to run once a day). Safe to run repeatedly: a
    festival already linked to an announcement (source_festival_id) is skipped,
    so re-running never creates a duplicate. The created row is an ordinary
    announcement - admins edit/delete it the same as any other."""

    def __init__(self, festival_repo: FestivalRepository, announcement_repo: AnnouncementRepository):
        self.festival_repo = festival_repo
        self.announcement_repo = announcement_repo

    def _is_due(self, festival: Festival, today: date) -> bool:
        if not festival.festival_date:
            return False
        announce_from = festival.festival_date - timedelta(days=festival.announce_days_before)
        last_day = festival.end_date or festival.festival_date
        return announce_from <= today <= last_day

    def generate_due_announcements(self, today: Optional[date] = None) -> List[Announcement]:
        today = today or date.today()
        created: List[Announcement] = []
        for festival in self.festival_repo.query_auto_announce_candidates():
            if not self._is_due(festival, today):
                continue
            if self.announcement_repo.get_by_source_festival(festival.id):
                continue
            created.append(self.announcement_repo.create(Announcement(
                title=festival.name,
                message=festival.description or f"{festival.name} at the temple.",
                start_date=today,
                end_date=festival.end_date or festival.festival_date,
                source_festival_id=festival.id,
            )))
        return created
