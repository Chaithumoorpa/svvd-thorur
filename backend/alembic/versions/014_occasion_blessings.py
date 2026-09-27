"""Occasion Blessings: a paid photo + occasion page, visible at a private
link for 7 days once the temple collects the fee at the counter.

Revision ID: 014_blessings
Revises: 013_occasion
Create Date: 2026-09-27
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "014_blessings"
down_revision: Union[str, None] = "013_occasion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE incomesourcetype ADD VALUE IF NOT EXISTS 'OCCASION_BLESSING'")

    # create_type=False: created once, explicitly, here - otherwise create_table
    # below emits a second, unchecked CREATE TYPE for the column and fails.
    blessing_payment_status = postgresql.ENUM(
        "PENDING", "PAID", name="blessingpaymentstatus", create_type=False,
    )
    blessing_payment_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "occasion_blessings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("reference_number", sa.String(), nullable=False, unique=True),
        sa.Column("devotee_name", sa.String(), nullable=False),
        sa.Column("mobile_number", sa.String(length=15), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("occasion", sa.String(length=100), nullable=False),
        sa.Column("occasion_date", sa.Date(), nullable=False),
        sa.Column("relation", sa.String(length=200), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("photo_url", sa.String(), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("payment_status", blessing_payment_status, nullable=False, server_default="PENDING"),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("collected_by_admin_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_occasion_blessings_id", "occasion_blessings", ["id"])
    op.create_index("ix_occasion_blessings_reference_number", "occasion_blessings", ["reference_number"])
    op.create_index("ix_occasion_blessings_mobile_number", "occasion_blessings", ["mobile_number"])


def downgrade() -> None:
    op.drop_index("ix_occasion_blessings_mobile_number", table_name="occasion_blessings")
    op.drop_index("ix_occasion_blessings_reference_number", table_name="occasion_blessings")
    op.drop_index("ix_occasion_blessings_id", table_name="occasion_blessings")
    op.drop_table("occasion_blessings")
    op.execute("DROP TYPE IF EXISTS blessingpaymentstatus")
    # OCCASION_BLESSING stays in incomesourcetype - Postgres can't drop enum
    # values, and by the time anyone downgrades, live rows may already use it.
