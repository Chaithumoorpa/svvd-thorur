"""Rename Occasion Blessings -> Abhishekam, add visibility + daily slot cap

Revision ID: 015_abhishekam
Revises: 014_blessings
Create Date: 2026-09-27

The standalone "Occasion Blessing" feature (merged minutes before this) is
folded into a proper Abhishekam booking: capped at DAILY_SLOT_CAP (7) per
date like the temple's paper register, with a public/private visibility
choice for the public yearly calendar. Deployed only moments ago with no
real bookings yet, so this is a straight rename rather than a data
migration.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "015_abhishekam"
down_revision: Union[str, None] = "014_blessings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Skipped when ABHISHEKAM already exists - left behind by downgrade(), which
    # can't remove an enum value - so a downgrade + re-upgrade still works.
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid
                WHERE t.typname = 'incomesourcetype' AND e.enumlabel = 'ABHISHEKAM'
            ) THEN
                ALTER TYPE incomesourcetype RENAME VALUE 'OCCASION_BLESSING' TO 'ABHISHEKAM';
            END IF;
        END $$;
    """)
    op.execute("ALTER TYPE blessingpaymentstatus RENAME TO abhishekampaymentstatus")

    op.rename_table("occasion_blessings", "abhishekams")
    op.execute("ALTER INDEX ix_occasion_blessings_id RENAME TO ix_abhishekams_id")
    op.execute("ALTER INDEX ix_occasion_blessings_reference_number RENAME TO ix_abhishekams_reference_number")
    op.execute("ALTER INDEX ix_occasion_blessings_mobile_number RENAME TO ix_abhishekams_mobile_number")

    abhishekam_visibility = postgresql.ENUM("PUBLIC", "PRIVATE", name="abhishekamvisibility", create_type=False)
    abhishekam_visibility.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "abhishekams",
        sa.Column("visibility", abhishekam_visibility, nullable=False, server_default="PRIVATE"),
    )
    op.create_index("ix_abhishekams_occasion_date", "abhishekams", ["occasion_date"])


def downgrade() -> None:
    op.drop_index("ix_abhishekams_occasion_date", table_name="abhishekams")
    op.drop_column("abhishekams", "visibility")
    op.execute("DROP TYPE IF EXISTS abhishekamvisibility")

    op.execute("ALTER INDEX ix_abhishekams_mobile_number RENAME TO ix_occasion_blessings_mobile_number")
    op.execute("ALTER INDEX ix_abhishekams_reference_number RENAME TO ix_occasion_blessings_reference_number")
    op.execute("ALTER INDEX ix_abhishekams_id RENAME TO ix_occasion_blessings_id")
    op.rename_table("abhishekams", "occasion_blessings")

    op.execute("ALTER TYPE abhishekampaymentstatus RENAME TO blessingpaymentstatus")
    # ABHISHEKAM stays in incomesourcetype - Postgres can't rename a value
    # back once other rows might reference it, and by the time anyone
    # downgrades, live rows may already use it.
