"""users.terms_accepted_at - proof a devotee agreed to Terms & the Privacy Policy at registration

Revision ID: 022_terms_accepted
Revises: 021_hide_dup_vinayaka
Create Date: 2026-09-29

Registration now requires ticking "I agree to the Terms & Conditions and
Privacy Policy" (both already exist as their own pages, linked from here
rather than duplicated). This records when - NULL for accounts created
before this change, or by an admin (POST /auth/admin/users), which was
never gated on it.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "022_terms_accepted"
down_revision: Union[str, None] = "021_hide_dup_vinayaka"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("terms_accepted_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "terms_accepted_at")
