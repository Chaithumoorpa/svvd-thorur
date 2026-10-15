"""users.email_verified_at: when the account proved it owns its email

Revision ID: 029_email_verified_at
Revises: 028_letter_authority_kinds
Create Date: 2026-10-15

Set when a sign-up confirms its emailed code, or a sign-in confirms its
emailed code. Backfill: staff/admin accounts (created by an admin) and any
account that has signed in (sign-in has required an emailed code for every
account with an email) count as verified. What stays NULL is a devotee
sign-up that never once signed in - the accounts self-registration used to
create without proving the email.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "029_email_verified_at"
down_revision: Union[str, None] = "028_letter_authority_kinds"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(), nullable=True))
    op.execute(
        "UPDATE users SET email_verified_at = COALESCE(last_login, created_at) "
        "WHERE email IS NOT NULL AND (last_login IS NOT NULL OR roles <> ARRAY['GENERAL_USER']::varchar[])"
    )


def downgrade() -> None:
    op.drop_column("users", "email_verified_at")
