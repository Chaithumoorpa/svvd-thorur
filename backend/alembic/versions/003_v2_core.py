"""SVVD 2.0 core: donations, audit log, timings, temple profile, Numeric money

Revision ID: 003_v2_core
Revises: 002_reconcile
Create Date: 2026-09-20

* `donations` table (one donor -> many donations); legacy per-donor gifts are copied in
* `audit_logs`, `temple_timings`
* extra public-profile columns on temples / temple_members / festivals / poojas / gallery
* money columns Integer -> Numeric(12,2) (lossless)
* seed rows for the temple profile and timings, taken from the previously hard-coded site
  content (only when the tables are empty)

Legacy donor columns (amount, donated_for, donated_on, receipt_*, payment_mode) are left in
place; a later revision may drop them once the copy has been verified.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_v2_core"
down_revision: Union[str, None] = "002_reconcile"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NOW = sa.text("now()")
MONEY = sa.Numeric(12, 2)


def _has_col(insp, table: str, col: str) -> bool:
    return any(c["name"] == col for c in insp.get_columns(table))


def _add_col(table: str, column: sa.Column) -> None:
    insp = sa.inspect(op.get_bind())
    if not _has_col(insp, table, column.name):
        op.add_column(table, column)


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # ---- new tables --------------------------------------------------------
    payment_mode = postgresql.ENUM("CASH", "UPI", "BANK", "CHEQUE", name="paymentmode", create_type=False)

    if not insp.has_table("donations"):
        op.create_table(
            "donations",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("donor_id", sa.Integer, sa.ForeignKey("donors.id"), nullable=False),
            sa.Column("amount", MONEY, nullable=False),
            sa.Column("donation_type", sa.String(50), nullable=False, server_default="general"),
            sa.Column("purpose", sa.Text()),
            sa.Column("donated_on", sa.DateTime(), nullable=False, server_default=NOW),
            sa.Column("receipt_number", sa.String(50), unique=True),
            sa.Column("receipt_generated_at", sa.DateTime()),
            sa.Column("payment_mode", payment_mode, nullable=False, server_default="CASH"),
            sa.Column("recorded_by_id", sa.Integer, sa.ForeignKey("users.id")),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=NOW),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=NOW),
        )
        op.create_index("ix_donations_id", "donations", ["id"])
        op.create_index("ix_donations_donor_id", "donations", ["donor_id"])
        op.create_index("ix_donations_donated_on", "donations", ["donated_on"])

        # Copy legacy gifts (donors.amount > 0) into donations.
        donor_cols = {c["name"] for c in insp.get_columns("donors")}
        if "amount" in donor_cols:
            receipt = "receipt_number" if "receipt_number" in donor_cols else "NULL"
            receipt_at = "receipt_generated_at" if "receipt_generated_at" in donor_cols else "NULL"
            mode = "COALESCE(payment_mode::text, 'CASH')::paymentmode" if "payment_mode" in donor_cols else "'CASH'::paymentmode"
            kind = "LEFT(COALESCE(NULLIF(donated_for, ''), 'general'), 50)" if "donated_for" in donor_cols else "'general'"
            donated_on = "donated_on" if "donated_on" in donor_cols else "created_at"
            op.execute(
                f"""
                INSERT INTO donations (donor_id, amount, donation_type, donated_on,
                                       receipt_number, receipt_generated_at, payment_mode)
                SELECT id, amount, {kind}, COALESCE({donated_on}, now()),
                       {receipt}, {receipt_at}, {mode}
                FROM donors WHERE amount IS NOT NULL AND amount > 0
                """
            )

    if not insp.has_table("audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("actor_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")),
            sa.Column("actor_username", sa.String(100)),
            sa.Column("action", sa.String(30), nullable=False),
            sa.Column("entity_type", sa.String(50), nullable=False),
            sa.Column("entity_id", sa.String(64)),
            sa.Column("summary", sa.String(500)),
            sa.Column("changes", sa.JSON()),
            sa.Column("ip_address", sa.String(64)),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=NOW),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=NOW),
        )
        op.create_index("ix_audit_logs_id", "audit_logs", ["id"])
        op.create_index("ix_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])
        op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    if not insp.has_table("temple_timings"):
        op.create_table(
            "temple_timings",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("label", sa.String(100), nullable=False),
            sa.Column("start_time", sa.Time(), nullable=False),
            sa.Column("end_time", sa.Time(), nullable=False),
            sa.Column("days", sa.String(100), nullable=False, server_default="Daily"),
            sa.Column("note", sa.String(300)),
            sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=NOW),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=NOW),
        )
        op.create_index("ix_temple_timings_id", "temple_timings", ["id"])

    # ---- new columns on existing tables ------------------------------------
    for name, length in [("tagline", 200), ("address", 300), ("pincode", 10), ("map_url", 500),
                         ("whatsapp_number", 20), ("hero_image_url", 500), ("facebook_url", 300),
                         ("instagram_url", 300), ("youtube_url", 300)]:
        _add_col("temples", sa.Column(name, sa.String(length)))

    _add_col("temple_members", sa.Column("show_on_website", sa.Boolean, nullable=False, server_default=sa.false()))
    _add_col("temple_members", sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"))
    _add_col("temple_members", sa.Column("photo_url", sa.String(500)))

    _add_col("festivals", sa.Column("end_date", sa.Date()))
    _add_col("festivals", sa.Column("location", sa.String(200)))
    _add_col("festivals", sa.Column("image_url", sa.String(500)))

    _add_col("poojas", sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"))
    _add_col("gallery", sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"))

    # ---- money: Integer -> Numeric(12,2) -------------------------------------
    for table, column in [("poojas", "suggested_amount"), ("seva_tickets", "amount"),
                          ("income_transactions", "amount"), ("expense_transactions", "amount")]:
        op.alter_column(table, column, type_=MONEY, existing_nullable=(column == "suggested_amount"),
                        postgresql_using=f"{column}::numeric(12,2)")

    # ---- indexes that back the new ORDER BY / filter paths -------------------
    op.create_index("ix_announcements_created_at", "announcements", ["created_at"], if_not_exists=True)
    op.create_index("ix_festivals_festival_date", "festivals", ["festival_date"], if_not_exists=True)
    op.create_index("ix_income_transactions_received_at", "income_transactions", ["received_at"], if_not_exists=True)
    op.create_index("ix_seva_tickets_seva_date", "seva_tickets", ["seva_date"], if_not_exists=True)
    op.create_index("ix_seva_tickets_status", "seva_tickets", ["status"], if_not_exists=True)
    op.create_index("ix_seva_tickets_mobile_number", "seva_tickets", ["mobile_number"], if_not_exists=True)
    op.create_index("ix_expense_transactions_expense_date", "expense_transactions", ["expense_date"], if_not_exists=True)

    # ---- seed content that used to be hard-coded in the frontend --------------
    op.execute(
        """
        INSERT INTO temples (name, deity_name, village, state, contact_email, map_url, is_active)
        SELECT 'Sri Varasiddhi Vinayaka Swamy Temple', 'Sri Varasiddhi Vinayaka Swamy',
               'Thorur', 'Andhra Pradesh', 'info@svvdthorur.org',
               'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d881002.5788503479!2d79.21050739825243!3d13.641851241157436!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3a4d5bc04479e687%3A0x9365d686a757f596!2ssri%20vinayaka%20temple!5e0!3m2!1sen!2sin!4v1766833981047!5m2!1sen!2sin',
               true
        WHERE NOT EXISTS (SELECT 1 FROM temples)
        """
    )
    op.execute(
        """
        INSERT INTO temple_timings (label, start_time, end_time, days, note, sort_order)
        SELECT v.label, v.st::time, v.et::time, 'Daily', v.note, v.so
        FROM (VALUES
            ('Morning Darshan', '06:00', '12:30', 'Suprabhatam 6:00 AM, Abhishekam 7:00 AM, Archana from 9:00 AM', 1),
            ('Evening Darshan', '16:30', '20:30', 'Archana 4:30 PM, Harathi 7:30 PM, Ekantha Seva 8:15 PM', 2)
        ) AS v(label, st, et, note, so)
        WHERE NOT EXISTS (SELECT 1 FROM temple_timings)
        """
    )


def downgrade() -> None:
    for table, column in [("poojas", "suggested_amount"), ("seva_tickets", "amount"),
                          ("income_transactions", "amount"), ("expense_transactions", "amount")]:
        op.alter_column(table, column, type_=sa.Integer(),
                        postgresql_using=f"round({column})::integer")
    for table, cols in [("gallery", ["sort_order"]), ("poojas", ["sort_order"]),
                        ("festivals", ["image_url", "location", "end_date"]),
                        ("temple_members", ["photo_url", "sort_order", "show_on_website"]),
                        ("temples", ["youtube_url", "instagram_url", "facebook_url", "hero_image_url",
                                     "whatsapp_number", "map_url", "pincode", "address", "tagline"])]:
        for col in cols:
            op.drop_column(table, col)
    op.drop_table("temple_timings")
    op.drop_table("audit_logs")
    op.drop_table("donations")
