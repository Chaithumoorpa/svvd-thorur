"""Festivals computed by the festival calendar carry a source_key

Revision ID: 020_festival_source_key
Revises: 019_blessing_review
Create Date: 2026-09-27

The festival calendar (app/services/festival_calendar.py) adds each upcoming
festival as an ordinary row; source_key (e.g. "sankashti-chaturthi:2026-10-29")
lets it skip ones it already added - including ones an admin has since hidden.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "020_festival_source_key"
down_revision: Union[str, None] = "019_blessing_review"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("festivals", sa.Column("source_key", sa.String(80), nullable=True))
    op.create_unique_constraint("uq_festivals_source_key", "festivals", ["source_key"])


def downgrade() -> None:
    op.drop_constraint("uq_festivals_source_key", "festivals", type_="unique")
    op.drop_column("festivals", "source_key")
