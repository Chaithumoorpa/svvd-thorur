"""FestivalAnnouncementService: turns a due festival into an announcement.
Runs entirely at the service layer (no HTTP round trip needed) since the
generator is invoked by a cron-run CLI script, not an API endpoint - admins
still edit/delete the resulting announcement through the ordinary endpoints,
covered by test_content.py."""
from datetime import date, timedelta

from app.models.announcement import Announcement
from app.models.festival import Festival
from app.repositories.announcement_repo import AnnouncementRepository
from app.repositories.festival_repo import FestivalRepository
from app.services.festival_announcement_service import FestivalAnnouncementService


def _festival(db, **overrides) -> Festival:
    festival = Festival(name=overrides.pop("name", "Sankashti Chaturthi - October"), **overrides)
    db.add(festival)
    db.commit()
    db.refresh(festival)
    return festival


def _service(db) -> FestivalAnnouncementService:
    return FestivalAnnouncementService(FestivalRepository(db), AnnouncementRepository(db))


def test_generates_announcement_for_a_festival_within_its_announce_window(db):
    today = date.today()
    _festival(db, festival_date=today + timedelta(days=1), announce_days_before=2)

    created = _service(db).generate_due_announcements(today)

    assert len(created) == 1
    assert created[0].title == "Sankashti Chaturthi - October"
    assert created[0].source_festival_id is not None


def test_skips_a_festival_outside_its_announce_window(db):
    today = date.today()
    _festival(db, festival_date=today + timedelta(days=10), announce_days_before=2)

    assert _service(db).generate_due_announcements(today) == []


def test_skips_a_festival_with_auto_announce_off(db):
    today = date.today()
    _festival(db, festival_date=today, announce_days_before=2, auto_announce=False)

    assert _service(db).generate_due_announcements(today) == []


def test_skips_an_inactive_festival(db):
    today = date.today()
    _festival(db, festival_date=today, announce_days_before=2, is_active=False)

    assert _service(db).generate_due_announcements(today) == []


def test_running_twice_does_not_duplicate(db):
    today = date.today()
    _festival(db, festival_date=today, announce_days_before=2)

    service = _service(db)
    first = service.generate_due_announcements(today)
    second = service.generate_due_announcements(today)

    assert len(first) == 1
    assert second == []
    assert db.query(Announcement).count() == 1


def test_multi_day_festival_stays_due_through_its_end_date(db):
    today = date.today()
    _festival(db, festival_date=today - timedelta(days=1), end_date=today + timedelta(days=1),
              announce_days_before=2)

    created = _service(db).generate_due_announcements(today)

    assert len(created) == 1
    assert created[0].end_date == today + timedelta(days=1)
