"""Fail if the migrated database is missing a column the models use.

pytest builds its SQLite schema straight from the models, so a migration that
forgets a column passes every test and then breaks the first INSERT in
production. CI runs this right after `alembic upgrade head` on Postgres.

    python -m app.cli.check_schema
"""
import sys

from sqlalchemy import create_engine, inspect

import app.models  # noqa: F401  (registers every model on Base.metadata)
from app.core.config import settings
from app.models.base import Base


def missing_columns(engine) -> list[str]:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    problems = []
    for table in Base.metadata.sorted_tables:
        if table.name not in tables:
            problems.append(f"table {table.name} is missing")
            continue
        existing = {c["name"] for c in inspector.get_columns(table.name)}
        problems += [f"{table.name}.{col.name} is missing" for col in table.columns if col.name not in existing]
    return problems


def main() -> int:
    problems = missing_columns(create_engine(settings.DATABASE_URL))
    for problem in problems:
        print(f"schema drift: {problem}", file=sys.stderr)
    if problems:
        print("The migrations don't create everything the models use - add a migration.", file=sys.stderr)
        return 1
    print("Schema matches the models.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
