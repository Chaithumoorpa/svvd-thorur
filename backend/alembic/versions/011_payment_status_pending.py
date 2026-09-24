"""Add PENDING to the paymentstatus enum

Revision ID: 011_payment_pending
Revises: 010_festival_auto
Create Date: 2026-09-24

A paid seva booked online (no payment gateway yet - see book_ticket) now
gets a ticket right away instead of being turned away to the counter; the
fee is collected in person and the ticket is PENDING until then. FREE stays
"no fee at all", so the finance ledger never confuses the two.

Postgres requires ALTER TYPE ... ADD VALUE for a native enum; safe to run
inside a normal transaction on Postgres 12+ since nothing in this migration
uses the new value. Downgrade is a no-op - Postgres has no ALTER TYPE ...
DROP VALUE, and by the time anyone downgrades, live rows may already use it.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "011_payment_pending"
down_revision: Union[str, None] = "010_festival_auto"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE paymentstatus ADD VALUE IF NOT EXISTS 'PENDING'")


def downgrade() -> None:
    pass
