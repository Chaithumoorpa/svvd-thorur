"""Sends the occasion blessing emails due today - seva bookings (Abhishekam
included) made for an occasion, on their seva date - and exits. Meant to run once a
day from cron on the EC2 host - see the "Occasion greetings" section of
DEPLOY_AWS.md for the crontab line. Idempotent: an already-greeted booking is
skipped, so re-running it (or re-running a failed day) never double-sends.

    docker compose exec -T backend python -m app.cli.send_occasion_greetings
"""
from datetime import date

from app.core.database import SessionLocal
from app.core.logging_config import setup_logging
from app.services.occasion_greeting_service import OccasionGreetingService

logger = setup_logging()


def main() -> None:
    db = SessionLocal()
    try:
        sent = OccasionGreetingService(db).send_due(date.today())
        logger.info("Occasion greetings sent: %d.", sent)
    finally:
        db.close()


if __name__ == "__main__":
    main()
