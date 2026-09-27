"""Indexes for the queries that scan whole growing tables today

Revision ID: 017_query_indexes
Revises: 016_greeting_sent_at
Create Date: 2026-09-27

Each index backs a specific query (see the model comments): the admin lists'
newest-first ordering, the ledger lookup behind every donation/ticket edit
or delete, filtering tickets by seva, and the repeated-deletion alert run on
every delete. Tables are small enough that a plain (locking) CREATE INDEX
finishes instantly.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "017_query_indexes"
down_revision: Union[str, None] = "016_greeting_sent_at"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEXES = [
    ("ix_income_transactions_reference_id", "income_transactions", ["reference_id"]),
    ("ix_seva_tickets_created_at", "seva_tickets", ["created_at"]),
    ("ix_seva_tickets_seva_id", "seva_tickets", ["seva_id"]),
    ("ix_contact_messages_created_at", "contact_messages", ["created_at"]),
    ("ix_audit_logs_actor_id_created_at", "audit_logs", ["actor_id", "created_at"]),
    ("ix_abhishekams_created_at", "abhishekams", ["created_at"]),
]


def upgrade() -> None:
    for name, table, columns in INDEXES:
        op.create_index(name, table, columns, if_not_exists=True)


def downgrade() -> None:
    for name, table, _ in reversed(INDEXES):
        op.drop_index(name, table_name=table, if_exists=True)
