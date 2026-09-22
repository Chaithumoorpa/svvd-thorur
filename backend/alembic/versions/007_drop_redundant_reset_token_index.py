"""Drop redundant unique index on password_reset_tokens.token_hash

Revision ID: 007_drop_redundant_idx
Revises: 006_password_reset
Create Date: 2026-09-22

006 declared `token_hash` both `unique=True` (which creates its own unique
constraint/index on the column) and a separate explicit unique index on the
same column - two identical unique indexes maintained on every write for no
benefit. This drops the redundant explicit one; the column-level unique
constraint (and its backing index) stays.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "007_drop_redundant_idx"
down_revision: Union[str, None] = "006_password_reset"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_password_reset_tokens_token_hash", table_name="password_reset_tokens")


def downgrade() -> None:
    op.create_index(
        "ix_password_reset_tokens_token_hash", "password_reset_tokens", ["token_hash"], unique=True
    )
