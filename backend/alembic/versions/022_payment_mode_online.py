"""Add ONLINE to the paymentmode enum

Revision ID: 022_payment_mode_online
Revises: 021_hide_dup_vinayaka
Create Date: 2026-09-28

Online payments (Razorpay) for donations and paid seva bookings post an
IncomeTransaction/Donation with payment_mode=ONLINE - a new value on the
existing paymentmode enum shared by donations, income_transactions and
expense_transactions.

Postgres requires ALTER TYPE ... ADD VALUE for a native enum; safe to run
inside a normal transaction on Postgres 12+ since nothing in this migration
uses the new value (same pattern as 011_payment_status_pending). Downgrade is
a no-op - Postgres has no ALTER TYPE ... DROP VALUE, and by the time anyone
downgrades, live rows may already use it.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "022_payment_mode_online"
down_revision: Union[str, None] = "021_hide_dup_vinayaka"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE paymentmode ADD VALUE IF NOT EXISTS 'ONLINE'")


def downgrade() -> None:
    pass
