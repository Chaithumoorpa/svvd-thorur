"""Fix temple name spelling: Varasiddhi -> Varasidhi

Revision ID: 012_temple_name_fix
Revises: 011_payment_pending
Create Date: 2026-09-24

The temple's own official registration documents (NGO Darpan, the
Charitable and Religious Trust Act registration, and the temple seal)
all spell it "Varasidhi" (one d), not "Varasiddhi" (two). This corrects
the already-seeded `temples` row(s) - a code-only fix (the hardcoded
fallback strings, the deity carousel, email templates) can't reach data
that was seeded before the correction; this migration is what does.
Idempotent and narrowly scoped: only touches rows that still have the
old spelling, and only the two columns that ever held it.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "012_temple_name_fix"
down_revision: Union[str, None] = "011_payment_pending"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE temples SET name = replace(name, 'Varasiddhi', 'Varasidhi') "
        "WHERE name LIKE '%Varasiddhi%'"
    )
    op.execute(
        "UPDATE temples SET deity_name = replace(deity_name, 'Varasiddhi', 'Varasidhi') "
        "WHERE deity_name LIKE '%Varasiddhi%'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE temples SET name = replace(name, 'Varasidhi', 'Varasiddhi') "
        "WHERE name LIKE '%Varasidhi%'"
    )
    op.execute(
        "UPDATE temples SET deity_name = replace(deity_name, 'Varasidhi', 'Varasiddhi') "
        "WHERE deity_name LIKE '%Varasidhi%'"
    )
