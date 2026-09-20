"""reconcile schema

Revision ID: 003_reconcile
Revises: 002_remaining_schema
Create Date: 2026-09-20

Brings ANY existing database (fresh 001_initial, or a legacy database created by
the deleted revisions 70f03626929a -> b385f6d4d9e5 -> c8f9a2b3d4e5) to the
pre-v2 schema WITHOUT touching existing data:

* creates tables that are missing
* adds columns that are missing (nullable unless a server default exists)
* gives legacy NOT NULL donor columns a default so new inserts keep working

Fully idempotent - safe to run on a database that is already up to date.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_reconcile"
down_revision: Union[str, None] = "002_remaining_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _enum(name: str, *values: str) -> postgresql.ENUM:
    return postgresql.ENUM(*values, name=name, create_type=False)


PAYMENT_MODE = _enum("paymentmode", "CASH", "UPI", "BANK", "CHEQUE")
EXPENSE_CATEGORY = _enum("expensecategory", "SALARY", "MATERIAL", "MAINTENANCE", "FESTIVAL", "OTHER")
INCOME_SOURCE = _enum("incomesourcetype", "SEVA", "DONATION", "HUNDI", "MANUAL")
CONTACT_STATUS = _enum("contactstatus", "PENDING", "IN_PROGRESS", "RESOLVED", "REJECTED")
PAYMENT_STATUS = _enum("paymentstatus", "FREE", "PAID")
TICKET_STATUS = _enum("ticketstatus", "ACTIVE", "USED", "CANCELLED")
TICKET_SOURCE = _enum("ticketsource", "ONLINE", "COUNTER")
ALL_ENUMS = [PAYMENT_MODE, EXPENSE_CATEGORY, INCOME_SOURCE, CONTACT_STATUS,
             PAYMENT_STATUS, TICKET_STATUS, TICKET_SOURCE]

NOW = sa.text("now()")


def _ts():
    return [
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=NOW),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=NOW),
    ]


def _tables(md: sa.MetaData) -> list[sa.Table]:
    """Frozen pre-v2 table definitions (do not import app models in migrations)."""
    T = lambda name, *cols: sa.Table(name, md, *cols)  # noqa: E731
    return [
        T("users",
          sa.Column("id", sa.Integer, primary_key=True),
          sa.Column("username", sa.String(100), nullable=False),
          sa.Column("email", sa.String(255)),
          sa.Column("phone", sa.String(20)),
          sa.Column("hashed_password", sa.String(255), nullable=False),
          sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
          sa.Column("roles", postgresql.ARRAY(sa.String()), nullable=False,
                    server_default=sa.text("'{\"GENERAL_USER\"}'")),
          sa.Column("last_login", sa.DateTime()),
          sa.Column("must_change_password", sa.Boolean, nullable=False, server_default=sa.false()),
          *_ts()),
        T("temple_members",
          sa.Column("id", sa.Integer, primary_key=True),
          sa.Column("name", sa.String(200), nullable=False),
          sa.Column("phone", sa.String(50), nullable=False, server_default=""),
          sa.Column("email", sa.String(200)),
          sa.Column("position", sa.String(100)),
          sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
          sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), unique=True),
          *_ts()),
        T("donors",
          sa.Column("id", sa.Integer, primary_key=True),
          sa.Column("name", sa.String(150), nullable=False),
          sa.Column("phone", sa.String(32)),
          sa.Column("email", sa.String(200)),
          sa.Column("address", sa.Text()),
          sa.Column("pan_number", sa.String(20)),
          sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
          *_ts()),
        T("announcements",
          sa.Column("id", sa.Integer, primary_key=True),
          sa.Column("title", sa.String(200), nullable=False),
          sa.Column("message", sa.Text()),
          sa.Column("start_date", sa.Date()),
          sa.Column("end_date", sa.Date()),
          sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
          sa.Column("created_by_id", sa.Integer, sa.ForeignKey("users.id")),
          *_ts()),
        T("temples",
          sa.Column("id", sa.Integer, primary_key=True),
          sa.Column("name", sa.String(150), nullable=False),
          sa.Column("deity_name", sa.String(100)),
          sa.Column("history", sa.Text()),
          sa.Column("village", sa.String(100)),
          sa.Column("district", sa.String(100)),
          sa.Column("state", sa.String(100)),
          sa.Column("contact_phone", sa.String(20)),
          sa.Column("contact_email", sa.String(100)),
          sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
          *_ts()),
        T("poojas",
          sa.Column("id", sa.Integer, primary_key=True),
          sa.Column("name", sa.String(100), nullable=False, unique=True),
          sa.Column("description", sa.Text()),
          sa.Column("start_time", sa.Time()),
          sa.Column("end_time", sa.Time()),
          sa.Column("pooja_type", sa.String(50), nullable=False, server_default="daily"),
          sa.Column("is_paid", sa.Boolean, nullable=False, server_default=sa.false()),
          sa.Column("suggested_amount", sa.Integer()),
          sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
          *_ts()),
        T("festivals",
          sa.Column("id", sa.Integer, primary_key=True),
          sa.Column("name", sa.String(150), nullable=False),
          sa.Column("description", sa.Text()),
          sa.Column("festival_date", sa.Date()),
          sa.Column("festival_type", sa.String(50), nullable=False, server_default="annual"),
          sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
          *_ts()),
        T("gallery",
          sa.Column("id", sa.Integer, primary_key=True),
          sa.Column("title", sa.String(), nullable=False),
          sa.Column("description", sa.Text()),
          sa.Column("image_url", sa.String(), nullable=False),
          sa.Column("category", sa.String(), nullable=False),
          sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
          sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id")),
          *_ts()),
        T("contact_messages",
          sa.Column("id", sa.Integer, primary_key=True),
          sa.Column("name", sa.String(100), nullable=False),
          sa.Column("email", sa.String(100), nullable=False),
          sa.Column("subject", sa.String(200), nullable=False),
          sa.Column("message", sa.Text(), nullable=False),
          sa.Column("status", CONTACT_STATUS, nullable=False, server_default="PENDING"),
          sa.Column("admin_notes", sa.Text()),
          *_ts()),
        T("seva_tickets",
          sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
          sa.Column("ticket_number", sa.String(), nullable=False, unique=True),
          sa.Column("seva_id", sa.Integer, sa.ForeignKey("poojas.id"), nullable=False),
          sa.Column("seva_name", sa.String(), nullable=False),
          sa.Column("devotee_name", sa.String(), nullable=False),
          sa.Column("mobile_number", sa.String(15), nullable=False),
          sa.Column("seva_date", sa.Date(), nullable=False),
          sa.Column("seva_time", sa.Time()),
          sa.Column("payment_status", PAYMENT_STATUS, nullable=False, server_default="FREE"),
          sa.Column("amount", sa.Integer, nullable=False, server_default="0"),
          sa.Column("status", TICKET_STATUS, nullable=False, server_default="ACTIVE"),
          sa.Column("source", TICKET_SOURCE, nullable=False, server_default="ONLINE"),
          sa.Column("created_by_admin_id", sa.Integer, sa.ForeignKey("users.id")),
          sa.Column("qr_token", sa.String(), nullable=False, unique=True),
          *_ts()),
        T("income_transactions",
          sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
          sa.Column("source_type", INCOME_SOURCE, nullable=False),
          sa.Column("reference_id", sa.String(255)),
          sa.Column("amount", sa.Integer, nullable=False),
          sa.Column("payment_mode", PAYMENT_MODE, nullable=False),
          sa.Column("received_by", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
          sa.Column("received_at", sa.DateTime(), nullable=False, server_default=NOW),
          sa.Column("notes", sa.Text()),
          *_ts()),
        T("expense_transactions",
          sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
          sa.Column("category", EXPENSE_CATEGORY, nullable=False),
          sa.Column("description", sa.String(255), nullable=False),
          sa.Column("amount", sa.Integer, nullable=False),
          sa.Column("payment_mode", PAYMENT_MODE, nullable=False),
          sa.Column("paid_to", sa.String(255), nullable=False),
          sa.Column("approved_by", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
          sa.Column("expense_date", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
          sa.Column("notes", sa.Text()),
          *_ts()),
        T("visitor_logs",
          sa.Column("id", sa.Integer, primary_key=True),
          sa.Column("ip_hash", sa.String(), nullable=False),
          sa.Column("visit_date", sa.Date(), nullable=False),
          *_ts()),
    ]


def _copy_legacy_members(bind, insp) -> None:
    """Legacy `members` (user-linked) -> `temple_members`, only if the latter is absent."""
    if insp.has_table("temple_members") or not insp.has_table("members"):
        return
    op.create_table(
        "temple_members",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(50), nullable=False, server_default=""),
        sa.Column("email", sa.String(200)),
        sa.Column("position", sa.String(100)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=NOW),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=NOW),
    )
    op.execute(
        """
        INSERT INTO temple_members (name, phone, email, position, is_active, user_id, created_at, updated_at)
        SELECT m.full_name, COALESCE(u.phone, ''), u.email, m.designation, m.is_active, m.user_id,
               m.created_at, m.updated_at
        FROM members m LEFT JOIN users u ON u.id = m.user_id
        """
    )


def _sync_table(bind, table: sa.Table) -> None:
    insp = sa.inspect(bind)
    if not insp.has_table(table.name):
        table.create(bind)
        return
    existing = {c["name"]: c for c in insp.get_columns(table.name)}
    for col in table.columns:
        if col.name in existing:
            # Legacy tables were created without server defaults; add them so plain SQL
            # inserts (seeds, admin scripts) work. Never changes existing values.
            if col.server_default is not None and existing[col.name].get("default") is None:
                op.alter_column(table.name, col.name, server_default=col.server_default.arg)
            continue
        new_col = col._copy()
        if new_col.server_default is None:
            new_col.nullable = True  # cannot add NOT NULL without default to populated table
        new_col.primary_key = False
        new_col.unique = None
        new_col.foreign_keys = set()
        op.add_column(table.name, new_col)


def upgrade() -> None:
    bind = op.get_bind()
    for enum in ALL_ENUMS:
        enum.create(bind, checkfirst=True)

    _copy_legacy_members(bind, sa.inspect(bind))

    md = sa.MetaData()
    tables = _tables(md)  # dependency order (users first)
    for table in tables:
        _sync_table(bind, table)

    # Legacy donors carried the gift itself (amount NOT NULL / donated_on NOT NULL, no default).
    # Give those columns defaults so inserting a bare donor keeps working; 003 moves the data
    # into `donations`.
    insp = sa.inspect(bind)
    donor_cols = {c["name"] for c in insp.get_columns("donors")}
    if "amount" in donor_cols:
        op.execute("ALTER TABLE donors ALTER COLUMN amount SET DEFAULT 0")
    if "donated_on" in donor_cols:
        op.execute("ALTER TABLE donors ALTER COLUMN donated_on SET DEFAULT now()")


def downgrade() -> None:
    # Reconciliation is additive and non-destructive; there is nothing safe to undo.
    pass
