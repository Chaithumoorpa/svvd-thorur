"""remaining tables and donor receipt fields

Revision ID: 002_remaining_schema
Revises: 001_initial
Create Date: 2026-09-20

Revision 001 only created users, temple_members, donors and announcements, but the
application also uses poojas, festivals, gallery, seva_tickets, contact_messages,
visitor_logs, temples, income_transactions and expense_transactions. On a fresh
database `alembic upgrade head` therefore produced a site where most endpoints
returned HTTP 500 ("relation ... does not exist").

This revision brings the schema in line with the models. It is idempotent: an
existing production database that already has some of these tables/columns (for
example created by an earlier, since-squashed migration history) is left alone and
only the missing pieces are added.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002_remaining_schema"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _enum(name: str, *values: str) -> postgresql.ENUM:
    # create_type=False: types are created once, explicitly, in _ensure_enums().
    # PaymentMode is shared by three tables, so implicit creation would fail with
    # "type paymentmode already exists".
    return postgresql.ENUM(*values, name=name, create_type=False)


CONTACT_STATUS = _enum("contactstatus", "PENDING", "IN_PROGRESS", "RESOLVED", "REJECTED")
EXPENSE_CATEGORY = _enum("expensecategory", "SALARY", "MATERIAL", "MAINTENANCE", "FESTIVAL", "OTHER")
INCOME_SOURCE = _enum("incomesourcetype", "SEVA", "DONATION", "HUNDI", "MANUAL")
PAYMENT_MODE = _enum("paymentmode", "CASH", "UPI", "BANK", "CHEQUE")
PAYMENT_STATUS = _enum("paymentstatus", "FREE", "PAID")
TICKET_STATUS = _enum("ticketstatus", "ACTIVE", "USED", "CANCELLED")
TICKET_SOURCE = _enum("ticketsource", "ONLINE", "COUNTER")

ALL_ENUMS = [
    CONTACT_STATUS, EXPENSE_CATEGORY, INCOME_SOURCE, PAYMENT_MODE,
    PAYMENT_STATUS, TICKET_STATUS, TICKET_SOURCE,
]


def _timestamps():
    now = sa.text("now()")
    return [
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=now),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=now),
    ]


def _table(bind, name: str, *columns_and_constraints, indexes=()):
    """Create `name` (plus indexes) only if it does not exist yet."""
    if name in sa.inspect(bind).get_table_names():
        return
    op.create_table(name, *columns_and_constraints, *_timestamps())
    for index_name, cols, unique in indexes:
        op.create_index(op.f(index_name), name, cols, unique=unique)


def upgrade() -> None:
    bind = op.get_bind()
    for enum in ALL_ENUMS:
        enum.create(bind, checkfirst=True)

    _table(
        bind, "contact_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", CONTACT_STATUS, nullable=False, server_default="PENDING"),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        indexes=[("ix_contact_messages_id", ["id"], False)],
    )
    _table(
        bind, "festivals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("festival_date", sa.Date(), nullable=True),
        sa.Column("festival_type", sa.String(length=50), nullable=False, server_default="annual"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id"),
        indexes=[("ix_festivals_id", ["id"], False)],
    )
    _table(
        bind, "poojas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("pooja_type", sa.String(length=50), nullable=False, server_default="daily"),
        sa.Column("is_paid", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("suggested_amount", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        indexes=[("ix_poojas_id", ["id"], False)],
    )
    _table(
        bind, "temples",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("deity_name", sa.String(length=100), nullable=True),
        sa.Column("history", sa.Text(), nullable=True),
        sa.Column("village", sa.String(length=100), nullable=True),
        sa.Column("district", sa.String(length=100), nullable=True),
        sa.Column("state", sa.String(length=100), nullable=True),
        sa.Column("contact_phone", sa.String(length=20), nullable=True),
        sa.Column("contact_email", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id"),
        indexes=[("ix_temples_id", ["id"], False)],
    )
    _table(
        bind, "visitor_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ip_hash", sa.String(), nullable=False),
        sa.Column("visit_date", sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        indexes=[
            ("ix_visitor_logs_id", ["id"], False),
            ("ix_visitor_logs_ip_hash", ["ip_hash"], False),
            ("ix_visitor_logs_visit_date", ["visit_date"], False),
        ],
    )
    _table(
        bind, "expense_transactions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("category", EXPENSE_CATEGORY, nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("payment_mode", PAYMENT_MODE, nullable=False),
        sa.Column("paid_to", sa.String(length=255), nullable=False),
        sa.Column("approved_by", sa.Integer(), nullable=False),
        sa.Column("expense_date", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        indexes=[
            ("ix_expense_transactions_category", ["category"], False),
            ("ix_expense_transactions_payment_mode", ["payment_mode"], False),
        ],
    )
    _table(
        bind, "gallery",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        indexes=[("ix_gallery_id", ["id"], False)],
    )
    _table(
        bind, "income_transactions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("source_type", INCOME_SOURCE, nullable=False),
        sa.Column("reference_id", sa.String(length=255), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("payment_mode", PAYMENT_MODE, nullable=False),
        sa.Column("received_by", sa.Integer(), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["received_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        indexes=[
            ("ix_income_transactions_payment_mode", ["payment_mode"], False),
            ("ix_income_transactions_source_type", ["source_type"], False),
        ],
    )
    _table(
        bind, "seva_tickets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ticket_number", sa.String(), nullable=False),
        sa.Column("seva_id", sa.Integer(), nullable=False),
        sa.Column("seva_name", sa.String(), nullable=False),
        sa.Column("devotee_name", sa.String(), nullable=False),
        sa.Column("mobile_number", sa.String(length=15), nullable=False),
        sa.Column("seva_date", sa.Date(), nullable=False),
        sa.Column("seva_time", sa.Time(), nullable=True),
        sa.Column("payment_status", PAYMENT_STATUS, nullable=False, server_default="FREE"),
        sa.Column("amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", TICKET_STATUS, nullable=False, server_default="ACTIVE"),
        sa.Column("source", TICKET_SOURCE, nullable=False, server_default="ONLINE"),
        sa.Column("created_by_admin_id", sa.Integer(), nullable=True),
        sa.Column("qr_token", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_admin_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["seva_id"], ["poojas.id"]),
        sa.PrimaryKeyConstraint("id"),
        indexes=[
            ("ix_seva_tickets_id", ["id"], False),
            ("ix_seva_tickets_mobile_number", ["mobile_number"], False),
            ("ix_seva_tickets_qr_token", ["qr_token"], True),
            ("ix_seva_tickets_seva_date", ["seva_date"], False),
            ("ix_seva_tickets_source", ["source"], False),
            ("ix_seva_tickets_status", ["status"], False),
            ("ix_seva_tickets_ticket_number", ["ticket_number"], True),
        ],
    )

    # Donor receipt fields (used by the receipt endpoints and PDF service).
    donor_columns = {c["name"] for c in sa.inspect(bind).get_columns("donors")}
    if "payment_mode" not in donor_columns:
        # server_default backfills existing donor rows as CASH.
        op.add_column("donors", sa.Column("payment_mode", PAYMENT_MODE, nullable=False, server_default="CASH"))
    if "receipt_number" not in donor_columns:
        op.add_column("donors", sa.Column("receipt_number", sa.String(length=50), nullable=True))
        op.create_unique_constraint("uq_donors_receipt_number", "donors", ["receipt_number"])
    if "receipt_generated_at" not in donor_columns:
        op.add_column("donors", sa.Column("receipt_generated_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    donor_columns = {c["name"] for c in sa.inspect(bind).get_columns("donors")}
    if "receipt_number" in donor_columns:
        op.drop_constraint("uq_donors_receipt_number", "donors", type_="unique")
        op.drop_column("donors", "receipt_number")
    for column in ("receipt_generated_at", "payment_mode"):
        if column in donor_columns:
            op.drop_column("donors", column)

    for table in (
        "seva_tickets", "income_transactions", "gallery", "expense_transactions",
        "visitor_logs", "temples", "poojas", "festivals", "contact_messages",
    ):
        op.execute(sa.text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))

    for enum in ALL_ENUMS:
        enum.drop(bind, checkfirst=True)
