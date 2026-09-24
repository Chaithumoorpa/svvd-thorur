"""Creates the day's due festival announcements (Sankashti Chaturthi and any
other festival/occasion with auto_announce on) and exits. Meant to run once a
day from cron on the EC2 host, the same way as deploy/aws/backup-db.sh - see
the "Festival announcements" section of DEPLOY_AWS.md for the crontab line.
Idempotent: a festival already linked to an announcement is skipped, so
running this more than once in a day (or re-running a failed day) is safe.

    docker compose exec -T backend python -m app.cli.generate_festival_announcements
"""
import logging

from app.core.database import SessionLocal
from app.core.logging_config import setup_logging
from app.repositories.announcement_repo import AnnouncementRepository
from app.repositories.festival_repo import FestivalRepository
from app.services.festival_announcement_service import FestivalAnnouncementService

logger = setup_logging()


def main() -> None:
    db = SessionLocal()
    try:
        service = FestivalAnnouncementService(FestivalRepository(db), AnnouncementRepository(db))
        created = service.generate_due_announcements()
        if created:
            logger.info("Generated %d festival announcement(s): %s",
                        len(created), ", ".join(a.title for a in created))
        else:
            logger.info("No festival announcements due today.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
