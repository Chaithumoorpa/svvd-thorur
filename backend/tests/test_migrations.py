"""
Regression tests for the migration bug: revision 001 only created 4 of 14 tables,
so a fresh `alembic upgrade head` gave a database on which most endpoints failed.
"""
import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text

from app.models.base import Base
from tests.conftest import alembic_config, engine


def _drift():
    with engine.connect() as conn:
        return compare_metadata(MigrationContext.configure(conn), Base.metadata)


def test_head_creates_every_model_table():
    tables = set(inspect(engine).get_table_names())
    missing = set(Base.metadata.tables) - tables
    assert not missing, f"tables defined in models but not created by migrations: {sorted(missing)}"


def test_schema_matches_models_no_drift():
    assert _drift() == [], "models and migrations disagree; generate a new migration"


def test_upgrade_is_safe_on_a_partially_migrated_database():
    """
    A production database may already contain some of these tables (older,
    since-squashed migration history). Upgrading must add only what is missing.
    """
    cfg = alembic_config()
    try:
        command.downgrade(cfg, "001_initial")
        with engine.begin() as conn:
            # Pre-create one of the later tables, as an old deployment might have.
            conn.execute(text(
                "CREATE TABLE festivals (id serial PRIMARY KEY, name varchar(150) NOT NULL,"
                " description text, festival_date date, festival_type varchar(50) NOT NULL"
                " DEFAULT 'annual', is_active boolean NOT NULL DEFAULT true,"
                " created_at timestamp NOT NULL DEFAULT now(),"
                " updated_at timestamp NOT NULL DEFAULT now())"
            ))
            conn.execute(text("CREATE INDEX ix_festivals_id ON festivals (id)"))
        command.upgrade(cfg, "head")
    finally:
        command.upgrade(cfg, "head")
    assert _drift() == []


def test_downgrade_then_upgrade_round_trip():
    cfg = alembic_config()
    command.downgrade(cfg, "001_initial")
    assert "seva_tickets" not in inspect(engine).get_table_names()
    command.upgrade(cfg, "head")
    assert _drift() == []


@pytest.mark.parametrize("column", ["receipt_number", "receipt_generated_at", "payment_mode", "amount"])
def test_donor_has_receipt_columns(column):
    assert column in {c["name"] for c in inspect(engine).get_columns("donors")}
