"""Staff review of public blessings and photos

Revision ID: 019_blessing_review
Revises: 018_seva_blessings
Create Date: 2026-09-27

Anyone with an email address can book a seva, so a devotee's occasion photo,
name and occasion no longer go on the website as submitted: photos upload to
a private S3 prefix (photo_key) and are published (photo_url) only when staff
approve them; review_status tracks PENDING -> APPROVED / REJECTED. Bookings
made before this - already asking to be shown or carrying a photo - start out
PENDING, i.e. hidden until reviewed.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "019_blessing_review"
down_revision: Union[str, None] = "018_seva_blessings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("seva_tickets", sa.Column("photo_key", sa.String(), nullable=True))
    op.add_column("seva_tickets", sa.Column("review_status", sa.String(10), nullable=True))
    op.create_index("ix_seva_tickets_review_status", "seva_tickets", ["review_status"])
    op.execute(
        "UPDATE seva_tickets SET review_status = 'PENDING' "
        "WHERE photo_url IS NOT NULL OR show_publicly"
    )


def downgrade() -> None:
    op.drop_index("ix_seva_tickets_review_status", table_name="seva_tickets")
    op.drop_column("seva_tickets", "review_status")
    op.drop_column("seva_tickets", "photo_key")
