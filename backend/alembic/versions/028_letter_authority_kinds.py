"""Letter types for authority documents: power of attorney, resolution, authorisation

Revision ID: 028_letter_authority_kinds
Revises: 027_official_letters
Create Date: 2026-10-14

Adds three values to the letterkind enum (ALTER TYPE ... ADD VALUE, safe in a
transaction on Postgres 12+ as nothing here uses them). Downgrade can't drop
enum values (Postgres has no DROP VALUE) - harmless, unused values.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "028_letter_authority_kinds"
down_revision: Union[str, None] = "027_official_letters"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_KINDS = ("POWER_OF_ATTORNEY", "RESOLUTION", "AUTHORISATION")


def upgrade() -> None:
    for value in NEW_KINDS:
        op.execute(f"ALTER TYPE letterkind ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    pass
