"""Temple inventory: consumable stock (ghee, oil, camphor, rice...) and the
register of valuables (ornaments, vessels, lamps...).

The quantity on an item is never edited directly - every change is a
StockMovement (purchase, donation in kind, usage, adjustment, write-off), so
the item's history always explains its current stock.
"""
import enum

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.types import MONEY_PRECISION, MONEY_SCALE

QTY = Numeric(14, 3)  # 3 decimals: 0.250 kg, 1.5 L


class ItemKind(str, enum.Enum):
    CONSUMABLE = "CONSUMABLE"  # used up: ghee, oil, flowers, rice
    ASSET = "ASSET"            # kept: ornaments, vessels, lamps, furniture


class AssetCondition(str, enum.Enum):
    GOOD = "GOOD"
    NEEDS_REPAIR = "NEEDS_REPAIR"
    DAMAGED = "DAMAGED"
    MISSING = "MISSING"


class MovementType(str, enum.Enum):
    PURCHASE = "PURCHASE"        # +qty, creates the matching expense
    DONATION_IN = "DONATION_IN"  # +qty, donated in kind (acknowledgement receipt)
    USAGE = "USAGE"              # -qty, used for a seva / festival / daily pooja
    ADJUSTMENT = "ADJUSTMENT"    # +/- qty, a physical count differs from the books
    WRITE_OFF = "WRITE_OFF"      # -qty, spoiled / expired / damaged / lost


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    kind = Column(Enum(ItemKind), nullable=False, index=True)
    category = Column(String(60), nullable=False, index=True)  # free text with suggestions in the UI
    unit = Column(String(20), nullable=False)                   # kg, g, L, ml, pcs, packets...
    quantity = Column(QTY, nullable=False, default=0, server_default="0")
    reorder_level = Column(QTY, nullable=True)                  # low-stock warning at or below this
    # Weighted average cost per unit across purchases and valued donations -
    # what one unit used for a festival is counted as costing.
    avg_unit_cost = Column(Numeric(14, 4), nullable=False, default=0, server_default="0")
    location = Column(String(150), nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")

    # ---- valuables (kind=ASSET) -----------------------------------------------------
    material = Column(String(40), nullable=True)                # GOLD, SILVER, BRASS, COPPER, PANCHALOHA...
    weight_grams = Column(Numeric(12, 3), nullable=True)
    estimated_value = Column(Numeric(MONEY_PRECISION, MONEY_SCALE), nullable=True)
    acquired_on = Column(Date, nullable=True)
    identification = Column(String(500), nullable=True)         # hallmarks, engravings, donor's inscription
    condition = Column(Enum(AssetCondition), nullable=True)
    photo_key = Column(String(255), nullable=True)              # private S3 key (receipts/inventory/...)
    last_verified_on = Column(Date, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=func.now(), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=True)

    movements = relationship("StockMovement", back_populates="item", cascade="all, delete-orphan",
                             order_by="StockMovement.id.desc()")


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(Enum(MovementType), nullable=False, index=True)
    quantity = Column(QTY, nullable=False)          # signed: + in, - out
    balance_after = Column(QTY, nullable=False)     # the item's stock right after this movement
    unit_cost = Column(Numeric(14, 4), nullable=True)
    total_value = Column(Numeric(MONEY_PRECISION, MONEY_SCALE), nullable=True)
    movement_date = Column(Date, nullable=False, index=True)
    notes = Column(String(500), nullable=True)

    # PURCHASE: the expense it created
    expense_id = Column(UUID(as_uuid=True), ForeignKey("expense_transactions.id", ondelete="SET NULL"), nullable=True)
    vendor = Column(String(255), nullable=True)
    # DONATION_IN: who gave it, and the acknowledgement receipt number
    donor_name = Column(String(150), nullable=True)
    donor_phone = Column(String(20), nullable=True)
    donor_address = Column(String(300), nullable=True)
    receipt_number = Column(String(30), nullable=True, unique=True)
    # USAGE: what it was used for
    pooja_id = Column(Integer, ForeignKey("poojas.id", ondelete="SET NULL"), nullable=True, index=True)
    festival_id = Column(Integer, ForeignKey("festivals.id", ondelete="SET NULL"), nullable=True, index=True)

    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=func.now(), server_default=func.now(), nullable=False)

    item = relationship("InventoryItem", back_populates="movements")


class AssetVerification(Base):
    """One physical check of a valuable: seen, weighed, condition noted."""
    __tablename__ = "asset_verifications"

    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False, index=True)
    verified_on = Column(Date, nullable=False)
    condition = Column(Enum(AssetCondition), nullable=False)
    weight_grams = Column(Numeric(12, 3), nullable=True)  # as weighed on the day
    notes = Column(String(500), nullable=True)
    verified_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=func.now(), server_default=func.now(), nullable=False)
