"""income_transactions.received_by is now nullable

Revision ID: 023_income_received_by_nullable
Revises: 022_payment_mode_online
Create Date: 2026-09-28

An online (Razorpay) payment for a donation or a seva ticket is collected
automatically - nobody on staff "received" it in the sense this column meant
until now (a counter payment, or a devotee's fee collected at the counter).
NULL means exactly that: collected online, not by a person.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "023_income_received_by_nullable"
down_revision: Union[str, None] = "022_payment_mode_online"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("income_transactions", "received_by", existing_type=sa.Integer(),
                    nullable=True, existing_nullable=False)


def downgrade() -> None:
    pass  # a NULL row from an online payment has no user to backfill
