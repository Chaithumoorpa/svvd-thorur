"""Occasion tagging for seva bookings and donations

Revision ID: 013_occasion
Revises: 012_temple_name_fix
Create Date: 2026-09-24

Adds a nullable `occasion` free-text column to `seva_tickets` and
`donations` - a devotee or the staff recording a donation can optionally
say what the booking/gift is for (a birthday, a wedding anniversary, ...),
which triggers a blessing email once the transaction is paid.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "013_occasion"
down_revision: Union[str, None] = "012_temple_name_fix"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("seva_tickets", sa.Column("occasion", sa.String(length=100), nullable=True))
    op.add_column("donations", sa.Column("occasion", sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column("donations", "occasion")
    op.drop_column("seva_tickets", "occasion")
