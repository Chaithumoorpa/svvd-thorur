"""Occasion blessing emails go out on the occasion's own date: track when
each one was sent

Revision ID: 016_greeting_sent_at
Revises: 015_abhishekam
Create Date: 2026-09-27
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "016_greeting_sent_at"
down_revision: Union[str, None] = "015_abhishekam"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("abhishekams", sa.Column("greeting_sent_at", sa.DateTime(), nullable=True))
    op.add_column("seva_tickets", sa.Column("greeting_sent_at", sa.DateTime(), nullable=True))
    # Seva occasion blessings used to go out the moment a seva was paid for (or
    # booked, if free). Mark those as already sent, or the new on-the-day
    # sending would email the same devotees a second time.
    op.execute(
        "UPDATE seva_tickets SET greeting_sent_at = updated_at "
        "WHERE occasion IS NOT NULL AND email IS NOT NULL AND payment_status IN ('FREE', 'PAID')"
    )


def downgrade() -> None:
    op.drop_column("seva_tickets", "greeting_sent_at")
    op.drop_column("abhishekams", "greeting_sent_at")
