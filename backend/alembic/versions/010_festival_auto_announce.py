"""Auto-generate announcements from upcoming festivals

Revision ID: 010_festival_auto
Revises: 009_ticket_user
Create Date: 2026-09-24

Adds `auto_announce` (default True) and `announce_days_before` (default 2)
to `festivals` - admin-editable opt-out and lead time per festival/occasion
(e.g. a monthly Sankashti Chaturthi row). Adds a nullable `source_festival_id`
FK on `announcements`, set on the row a daily job creates from a due
festival, so the job never creates a duplicate and admins can tell an
auto-generated announcement apart - it stays an ordinary announcement,
editable/deletable exactly like any other.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "010_festival_auto"
down_revision: Union[str, None] = "009_ticket_user"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("festivals", sa.Column("auto_announce", sa.Boolean(), nullable=False, server_default="true"))
    op.add_column("festivals", sa.Column("announce_days_before", sa.Integer(), nullable=False, server_default="2"))

    op.add_column("announcements", sa.Column("source_festival_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_announcements_source_festival_id", "announcements", "festivals",
        ["source_festival_id"], ["id"],
    )
    op.create_index("ix_announcements_source_festival_id", "announcements", ["source_festival_id"])


def downgrade() -> None:
    op.drop_index("ix_announcements_source_festival_id", table_name="announcements")
    op.drop_constraint("fk_announcements_source_festival_id", "announcements", type_="foreignkey")
    op.drop_column("announcements", "source_festival_id")

    op.drop_column("festivals", "announce_days_before")
    op.drop_column("festivals", "auto_announce")
