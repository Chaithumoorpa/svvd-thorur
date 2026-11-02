"""Expense approval workflow + budgets, and temple inventory

Revision ID: 026_expenses_inventory
Revises: 025_temple_trust_details
Create Date: 2026-10-14

expense_transactions gains a status (existing rows are APPROVED - they were
all entered by admins, who approve on entry), who submitted / decided /
voided it, a private bill photo key and an optional festival. New tables:
expense_budgets, inventory_items, stock_movements, asset_verifications.

New expensecategory values are added with ALTER TYPE ... ADD VALUE (safe in
a transaction on Postgres 12+ as nothing here uses them). Downgrade drops
the new tables/columns/types but cannot remove enum values (Postgres has no
DROP VALUE) - harmless, unused values.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "026_expenses_inventory"
down_revision: Union[str, None] = "025_temple_trust_details"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_CATEGORIES = ("POOJA_SUPPLIES", "ANNADANAM", "UTILITIES", "CONSTRUCTION", "ASSETS")

# create_type=False everywhere: each type is created once, explicitly, below -
# otherwise create_table/add_column would try to create it again (see 014).
expense_status = postgresql.ENUM("PENDING", "APPROVED", "REJECTED", "VOID", name="expensestatus", create_type=False)
item_kind = postgresql.ENUM("CONSUMABLE", "ASSET", name="itemkind", create_type=False)
asset_condition = postgresql.ENUM("GOOD", "NEEDS_REPAIR", "DAMAGED", "MISSING", name="assetcondition", create_type=False)
movement_type = postgresql.ENUM("PURCHASE", "DONATION_IN", "USAGE", "ADJUSTMENT", "WRITE_OFF",
                                name="movementtype", create_type=False)
expense_category = postgresql.ENUM(name="expensecategory", create_type=False)

QTY = sa.Numeric(14, 3)
MONEY = sa.Numeric(12, 2)


def _timestamps():
    """created_at / updated_at, which app.models.base.Base gives every table."""
    return (sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()))


def upgrade() -> None:
    bind = op.get_bind()
    for value in NEW_CATEGORIES:
        op.execute(f"ALTER TYPE expensecategory ADD VALUE IF NOT EXISTS '{value}'")
    for enum in (expense_status, item_kind, asset_condition, movement_type):
        enum.create(bind, checkfirst=True)

    # ---- expense workflow --------------------------------------------------------------
    op.add_column("expense_transactions", sa.Column("status", expense_status, nullable=False, server_default="APPROVED"))
    op.create_index("ix_expense_transactions_status", "expense_transactions", ["status"])
    op.alter_column("expense_transactions", "approved_by", existing_type=sa.Integer(), nullable=True)
    for col in ("submitted_by", "voided_by"):
        op.add_column("expense_transactions", sa.Column(col, sa.Integer(), nullable=True))
        op.create_foreign_key(f"fk_expense_transactions_{col}", "expense_transactions", "users", [col], ["id"],
                              ondelete="SET NULL")
    op.add_column("expense_transactions", sa.Column("decided_at", sa.DateTime(), nullable=True))
    op.add_column("expense_transactions", sa.Column("rejection_reason", sa.String(500), nullable=True))
    op.add_column("expense_transactions", sa.Column("voided_at", sa.DateTime(), nullable=True))
    op.add_column("expense_transactions", sa.Column("void_reason", sa.String(500), nullable=True))
    op.add_column("expense_transactions", sa.Column("bill_key", sa.String(255), nullable=True))
    op.add_column("expense_transactions", sa.Column("festival_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_expense_transactions_festival_id", "expense_transactions", "festivals",
                          ["festival_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_expense_transactions_festival_id", "expense_transactions", ["festival_id"])
    # Every existing expense was entered (and so approved) by an admin.
    op.execute("UPDATE expense_transactions SET submitted_by = approved_by, decided_at = created_at")

    op.create_table(
        "expense_budgets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("month", sa.Date(), nullable=False, index=True),
        sa.Column("category", expense_category, nullable=False),
        sa.Column("amount", MONEY, nullable=False),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("month", "category", name="uq_expense_budget_month_category"),
    )

    # ---- inventory ----------------------------------------------------------------------
    op.create_table(
        "inventory_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("kind", item_kind, nullable=False, index=True),
        sa.Column("category", sa.String(60), nullable=False, index=True),
        sa.Column("unit", sa.String(20), nullable=False),
        sa.Column("quantity", QTY, nullable=False, server_default="0"),
        sa.Column("reorder_level", QTY, nullable=True),
        sa.Column("avg_unit_cost", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("location", sa.String(150), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("material", sa.String(40), nullable=True),
        sa.Column("weight_grams", sa.Numeric(12, 3), nullable=True),
        sa.Column("estimated_value", MONEY, nullable=True),
        sa.Column("acquired_on", sa.Date(), nullable=True),
        sa.Column("identification", sa.String(500), nullable=True),
        sa.Column("condition", asset_condition, nullable=True),
        sa.Column("photo_key", sa.String(255), nullable=True),
        sa.Column("last_verified_on", sa.Date(), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        *_timestamps(),
    )
    op.create_table(
        "stock_movements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("inventory_items.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("type", movement_type, nullable=False, index=True),
        sa.Column("quantity", QTY, nullable=False),
        sa.Column("balance_after", QTY, nullable=False),
        sa.Column("unit_cost", sa.Numeric(14, 4), nullable=True),
        sa.Column("total_value", MONEY, nullable=True),
        sa.Column("movement_date", sa.Date(), nullable=False, index=True),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("expense_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("expense_transactions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("vendor", sa.String(255), nullable=True),
        sa.Column("donor_name", sa.String(150), nullable=True),
        sa.Column("donor_phone", sa.String(20), nullable=True),
        sa.Column("donor_address", sa.String(300), nullable=True),
        sa.Column("receipt_number", sa.String(30), nullable=True, unique=True),
        sa.Column("pooja_id", sa.Integer(), sa.ForeignKey("poojas.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("festival_id", sa.Integer(), sa.ForeignKey("festivals.id", ondelete="SET NULL"),
                  nullable=True, index=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        *_timestamps(),
    )
    op.create_table(
        "asset_verifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("inventory_items.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("verified_on", sa.Date(), nullable=False),
        sa.Column("condition", asset_condition, nullable=False),
        sa.Column("weight_grams", sa.Numeric(12, 3), nullable=True),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("verified_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        *_timestamps(),
    )


def downgrade() -> None:
    op.drop_table("asset_verifications")
    op.drop_table("stock_movements")
    op.drop_table("inventory_items")
    op.drop_table("expense_budgets")

    op.drop_index("ix_expense_transactions_festival_id", table_name="expense_transactions")
    op.drop_constraint("fk_expense_transactions_festival_id", "expense_transactions", type_="foreignkey")
    for col in ("submitted_by", "voided_by"):
        op.drop_constraint(f"fk_expense_transactions_{col}", "expense_transactions", type_="foreignkey")
    for col in ("festival_id", "bill_key", "void_reason", "voided_at", "voided_by",
                "rejection_reason", "decided_at", "submitted_by"):
        op.drop_column("expense_transactions", col)
    # Only approved expenses survive a downgrade - the old schema can't tell
    # pending/rejected/void rows from real spending.
    op.execute("DELETE FROM expense_transactions WHERE status <> 'APPROVED' OR approved_by IS NULL")
    op.alter_column("expense_transactions", "approved_by", existing_type=sa.Integer(), nullable=False)
    op.drop_index("ix_expense_transactions_status", table_name="expense_transactions")
    op.drop_column("expense_transactions", "status")

    bind = op.get_bind()
    for enum in (movement_type, asset_condition, item_kind, expense_status):
        enum.drop(bind, checkfirst=True)
