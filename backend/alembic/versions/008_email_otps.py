"""Email OTP codes for online seva ticket booking

Revision ID: 008_email_otps
Revises: 007_drop_redundant_idx
Create Date: 2026-09-22

Adds `email_otps` (one-time verification codes, only the SHA-256 hash
stored) and a nullable `email` column on `seva_tickets`, captured once
verified for online bookings; counter tickets leave it null.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008_email_otps"
down_revision: Union[str, None] = "007_drop_redundant_idx"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NOW = sa.text("now()")


def upgrade() -> None:
    op.create_table(
        "email_otps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("purpose", sa.String(length=50), nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=NOW),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=NOW),
    )
    op.create_index("ix_email_otps_email", "email_otps", ["email"])

    op.add_column("seva_tickets", sa.Column("email", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("seva_tickets", "email")
    op.drop_index("ix_email_otps_email", table_name="email_otps")
    op.drop_table("email_otps")
