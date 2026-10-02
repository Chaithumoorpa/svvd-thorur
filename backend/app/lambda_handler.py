"""AWS Lambda entry point (backend/Dockerfile.lambda: CMD ["app.lambda_handler.handler"]).

- API Gateway / Function URL events are served by the FastAPI app through Mangum.
- A direct invocation with the payload {"task": "<name>"} runs one maintenance job
  instead: the deploy pipeline runs "migrate" this way, and EventBridge Scheduler
  runs the daily jobs that were crontab lines on the EC2 host. HTTP requests always
  arrive wrapped in an API Gateway event (with "requestContext"), so only an IAM
  principal allowed lambda:InvokeFunction can reach the task path.
"""
import os
import time

# The app compares against naive date.today()/datetime.now() in many places
# (booking dates, receipts, "today's" announcements) and was always run with
# TZ=Asia/Kolkata. Lambda defaults to UTC, which would make "today" yesterday
# between 00:00 and 05:30 IST. Must run before anything reads the clock.
os.environ["TZ"] = "Asia/Kolkata"
time.tzset()
if time.timezone != -19800:
    raise RuntimeError("Asia/Kolkata zone data missing from the image (tzdata)")

import logging  # noqa: E402

from mangum import Mangum  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.migration_validator import check_migrations_on_startup, get_current_revision  # noqa: E402
from app.main import app  # noqa: E402

logger = logging.getLogger(__name__)

# Mangum runs the ASGI lifespan around *every* invocation, so the app's startup
# hook (this same check) would add a DB round-trip to each request. Run it once
# per container instead. Fatal only for multiple migration heads (a code bug);
# a database behind head is just logged, so the "migrate" task still works.
check_migrations_on_startup(
    alembic_config_path=settings.ALEMBIC_CONFIG,
    database_url=settings.DATABASE_URL,
    is_production=settings.is_production,
)

_http = Mangum(app, lifespan="off")


def _migrate() -> dict:
    from alembic import command
    from alembic.config import Config

    from app.core.legacy_stamp import restamp_legacy

    restamp_legacy(settings.DATABASE_URL)
    command.upgrade(Config(settings.ALEMBIC_CONFIG), "head")
    return {"revision": get_current_revision(settings.DATABASE_URL)}


def _send_occasion_greetings() -> dict:
    from app.cli.send_occasion_greetings import main

    main()
    return {}


def _generate_festival_announcements() -> dict:
    from app.cli.generate_festival_announcements import main

    main()
    return {}


TASKS = {
    "migrate": _migrate,
    "send_occasion_greetings": _send_occasion_greetings,
    "generate_festival_announcements": _generate_festival_announcements,
}


def handler(event, context):
    if isinstance(event, dict) and "task" in event and "requestContext" not in event:
        name = event["task"]
        task = TASKS.get(name)
        if task is None:
            raise ValueError(f"Unknown task {name!r}; expected one of {sorted(TASKS)}")
        logger.warning("Running task %s", name)
        return {"task": name, "ok": True, **task()}
    return _http(event, context)
