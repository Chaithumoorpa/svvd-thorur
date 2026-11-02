"""Temple.tv_sections: which sections the lobby TV (/tv) shows.

Revision ID: 030_temple_tv_sections
Revises: 029_email_verified_at
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "030_temple_tv_sections"
down_revision: Union[str, None] = "029_email_verified_at"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("temples", sa.Column("tv_sections", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("temples", "tv_sections")
