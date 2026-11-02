"""users.token_version - lets a sign-out end every session of the user

Revision ID: 024_user_token_version
Revises: 023_temple_upi_vpa
Create Date: 2026-10-06

Session tokens carry the user's token_version; logout, password change or
reset, and deactivation increment it, so tokens issued before stop working
immediately instead of living until they expire.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "024_user_token_version"
down_revision: Union[str, None] = "023_temple_upi_vpa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("token_version", sa.Integer(), server_default="0", nullable=False))


def downgrade() -> None:
    op.drop_column("users", "token_version")
