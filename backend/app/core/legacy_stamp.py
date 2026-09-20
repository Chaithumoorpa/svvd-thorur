"""
Re-stamp databases created by the deleted legacy Alembic revisions.

Before SVVD 2.0 the migration history was squashed into `001_initial`. A database that
was migrated by the old chain has `alembic_version` pointing at a revision id that no
longer exists, which makes `alembic upgrade head` fail with "Can't locate revision".
The additive reconcile migration (002) brings such a database to the current schema,
so stamping it as `001_initial` first is safe and loses no data.

Run before `alembic upgrade head` (entrypoint.sh does this).
"""
import logging
import sys

from sqlalchemy import create_engine, text

from app.core.config import settings

logger = logging.getLogger(__name__)

LEGACY_REVISIONS = {"70f03626929a", "b385f6d4d9e5", "c8f9a2b3d4e5"}
BASELINE = "001_initial"


def restamp_legacy(database_url: str) -> bool:
    engine = create_engine(database_url)
    try:
        with engine.begin() as conn:
            exists = conn.execute(text("SELECT to_regclass('alembic_version')")).scalar()
            if not exists:
                return False
            rows = conn.execute(text("SELECT version_num FROM alembic_version")).scalars().all()
            if not rows or not set(rows) <= LEGACY_REVISIONS:
                return False
            conn.execute(text("DELETE FROM alembic_version"))
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES (:v)"), {"v": BASELINE})
            logger.warning("Re-stamped legacy alembic revision(s) %s -> %s", rows, BASELINE)
            return True
    finally:
        engine.dispose()


if __name__ == "__main__":
    changed = restamp_legacy(settings.DATABASE_URL)
    print("legacy alembic revision re-stamped" if changed else "no legacy alembic revision found")
    sys.exit(0)
