"""temples: bank account name, trust registration, PAN and 80G numbers

Revision ID: 025_temple_trust_details
Revises: 024_user_token_version
Create Date: 2026-10-13

Printed on the e-Hundi page and its poster so a devotee can check they are
paying the registered temple, and see that the offering qualifies for 80G.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "025_temple_trust_details"
down_revision: Union[str, None] = "024_user_token_version"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("temples", sa.Column("bank_account_name", sa.String(length=150), nullable=True))
    op.add_column("temples", sa.Column("registration_number", sa.String(length=100), nullable=True))
    op.add_column("temples", sa.Column("pan_number", sa.String(length=10), nullable=True))
    op.add_column("temples", sa.Column("eighty_g_number", sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column("temples", "eighty_g_number")
    op.drop_column("temples", "pan_number")
    op.drop_column("temples", "registration_number")
    op.drop_column("temples", "bank_account_name")
