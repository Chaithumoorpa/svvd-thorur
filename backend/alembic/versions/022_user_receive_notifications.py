"""users.receive_notifications - opt-out flag for bulk devotee emails

Revision ID: 022_user_receive_notifications
Revises: 021_hide_dup_vinayaka
Create Date: 2026-09-29

Darshan-timing and announcement broadcasts (notify_devotees) go to every
devotee with an email on file. This adds a per-user opt-out, defaulting to
True (unchanged behaviour) so existing devotees keep getting notified until
they click "unsubscribe" in one of those emails.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "022_user_receive_notifications"
down_revision: Union[str, None] = "021_hide_dup_vinayaka"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("receive_notifications", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.alter_column("users", "receive_notifications", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "receive_notifications")
