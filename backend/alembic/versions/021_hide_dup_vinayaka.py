"""Hide the monthly Vinayaka Chaturthi that duplicated Ganesh Chaturthi

Revision ID: 021_hide_dup_vinayaka
Revises: 020_festival_source_key
Create Date: 2026-09-27

Bhadrapada's monthly Vinayaka Chaturthi is Ganesh Chaturthi itself, which the
calendar lists on its own; it no longer generates the monthly one for that
month. Rows it already added the same day as a Ganesh Chaturthi are hidden
(not deleted, so the calendar won't re-add them).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "021_hide_dup_vinayaka"
down_revision: Union[str, None] = "020_festival_source_key"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        UPDATE festivals SET is_active = false
        WHERE source_key LIKE 'vinayaka-chaturthi:%'
          AND festival_date IN (
              SELECT festival_date FROM festivals WHERE source_key LIKE 'ganesh-chaturthi:%'
          )
    """)


def downgrade() -> None:
    pass  # hiding a duplicate isn't worth undoing
