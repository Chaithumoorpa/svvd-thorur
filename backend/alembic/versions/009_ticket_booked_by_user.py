"""Link online seva bookings to a devotee account, when one is logged in

Revision ID: 009_ticket_user
Revises: 008_email_otps
Create Date: 2026-09-24

Adds a nullable `booked_by_user_id` FK on `seva_tickets` -> `users.id`, set
when an online booking is made while the devotee is signed in (anonymous
bookings, and all counter tickets, leave it null). Powers "My Bookings".
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009_ticket_user"
down_revision: Union[str, None] = "008_email_otps"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("seva_tickets", sa.Column("booked_by_user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_seva_tickets_booked_by_user_id", "seva_tickets", "users",
        ["booked_by_user_id"], ["id"],
    )
    op.create_index("ix_seva_tickets_booked_by_user_id", "seva_tickets", ["booked_by_user_id"])


def downgrade() -> None:
    op.drop_index("ix_seva_tickets_booked_by_user_id", table_name="seva_tickets")
    op.drop_constraint("fk_seva_tickets_booked_by_user_id", "seva_tickets", type_="foreignkey")
    op.drop_column("seva_tickets", "booked_by_user_id")
