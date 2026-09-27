"""Abhishekam is the temple's own seva: bookings per day, public blessings

Revision ID: 018_seva_blessings
Revises: 017_query_indexes
Create Date: 2026-09-27

The standalone Rs 50 Abhishekam booking (014-017) is folded into ordinary
seva booking: a seva can cap its bookings per date, and can let devotees add
an occasion photo and show their blessing publicly. The temple's existing
"Abhishekam" seva gets both - 7 a day, like its paper register.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "018_seva_blessings"
down_revision: Union[str, None] = "017_query_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("poojas", sa.Column("daily_slot_cap", sa.Integer(), nullable=True))
    op.add_column("poojas", sa.Column("public_blessings", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("seva_tickets", sa.Column("photo_url", sa.String(), nullable=True))
    op.add_column("seva_tickets", sa.Column("show_publicly", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.execute(
        "UPDATE poojas SET daily_slot_cap = 7, public_blessings = true WHERE lower(trim(name)) = 'abhishekam'"
    )

    # The standalone booking's table goes if nobody ever booked through it
    # (it was live only a few hours); a table with rows is left untouched.
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM abhishekams) THEN
                DROP TABLE abhishekams;
                DROP TYPE abhishekampaymentstatus;
                DROP TYPE abhishekamvisibility;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.drop_column("seva_tickets", "show_publicly")
    op.drop_column("seva_tickets", "photo_url")
    op.drop_column("poojas", "public_blessings")
    op.drop_column("poojas", "daily_slot_cap")

    # Put the standalone table back (empty) as 014-017 left it, so their own
    # downgrades still find it.
    op.execute("""
        DO $$
        BEGIN
            IF to_regclass('abhishekams') IS NULL THEN
                CREATE TYPE abhishekampaymentstatus AS ENUM ('PENDING', 'PAID');
                CREATE TYPE abhishekamvisibility AS ENUM ('PUBLIC', 'PRIVATE');
                CREATE TABLE abhishekams (
                    id UUID PRIMARY KEY,
                    reference_number VARCHAR NOT NULL UNIQUE,
                    devotee_name VARCHAR NOT NULL,
                    mobile_number VARCHAR(15) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    occasion VARCHAR(100) NOT NULL,
                    occasion_date DATE NOT NULL,
                    relation VARCHAR(200),
                    message TEXT,
                    photo_url VARCHAR NOT NULL,
                    amount NUMERIC(10, 2) NOT NULL,
                    payment_status abhishekampaymentstatus NOT NULL DEFAULT 'PENDING',
                    paid_at TIMESTAMP,
                    collected_by_admin_id INTEGER REFERENCES users (id),
                    created_at TIMESTAMP NOT NULL DEFAULT now(),
                    updated_at TIMESTAMP NOT NULL DEFAULT now(),
                    visibility abhishekamvisibility NOT NULL DEFAULT 'PRIVATE',
                    greeting_sent_at TIMESTAMP
                );
                CREATE INDEX ix_abhishekams_id ON abhishekams (id);
                CREATE INDEX ix_abhishekams_reference_number ON abhishekams (reference_number);
                CREATE INDEX ix_abhishekams_mobile_number ON abhishekams (mobile_number);
                CREATE INDEX ix_abhishekams_occasion_date ON abhishekams (occasion_date);
                CREATE INDEX ix_abhishekams_created_at ON abhishekams (created_at);
            END IF;
        END $$;
    """)
