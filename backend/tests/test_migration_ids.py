"""alembic_version.version_num is VARCHAR(32): a longer revision id passes on
SQLite but fails `alembic upgrade` on Postgres - after every earlier migration
in the same run has already been applied."""
import re
from pathlib import Path

VERSIONS = Path(__file__).resolve().parents[1] / "alembic" / "versions"


def test_every_revision_id_fits_alembic_version():
    ids = {f.name: re.search(r'^revision: str = ["\']([^"\']+)["\']', f.read_text(), re.M).group(1)
           for f in VERSIONS.glob("*.py")}
    assert ids, "no migrations found"
    too_long = {name: rid for name, rid in ids.items() if len(rid) > 32}
    assert not too_long
