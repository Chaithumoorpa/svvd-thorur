from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

from app.models.finance import ExpenseCategory, ExpenseStatus, PaymentMode
from app.models.inventory import AssetCondition, ItemKind, MovementType
from app.schemas.common import MoneyIn, MoneyInOrZero, MoneyOut, blank_to_none
from app.schemas.finance import BillKey

# Asset photos live privately under receipts/ (the prefix the server's IAM role can
# already write and read - see EXPENSE_BILL_PREFIX).
INVENTORY_PHOTO_PREFIX = "receipts/inventory"
PhotoKey = Annotated[str, StringConstraints(pattern=rf"^{INVENTORY_PHOTO_PREFIX}/[0-9a-f]{{32}}\.(jpg|png|webp|gif)$")]

Qty = Annotated[Decimal, Field(gt=0, le=Decimal("999999999"), max_digits=12, decimal_places=3)]
QtyOrZero = Annotated[Decimal, Field(ge=0, le=Decimal("999999999"), max_digits=12, decimal_places=3)]
Grams = Annotated[Decimal, Field(gt=0, le=Decimal("99999999"), max_digits=11, decimal_places=3)]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=150)]
Short = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
Unit = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]
Reason = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=500)]
Phone = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\+?[0-9 \-]{7,20}$")]

_BLANKABLE = ("location", "notes", "material", "identification", "photo_key")


def _not_future(v: Optional[date]) -> Optional[date]:
    if v and v > date.today():
        raise ValueError("The date can't be in the future")
    return v


# ---- items ------------------------------------------------------------------------------
class ItemFields(BaseModel):
    category: Optional[Short] = None
    unit: Optional[Unit] = None
    reorder_level: Optional[QtyOrZero] = None
    location: Optional[str] = Field(default=None, max_length=150)
    notes: Optional[str] = Field(default=None, max_length=2000)
    # valuables
    material: Optional[str] = Field(default=None, max_length=40)
    weight_grams: Optional[Grams] = None
    estimated_value: Optional[MoneyInOrZero] = None
    acquired_on: Optional[date] = None
    identification: Optional[str] = Field(default=None, max_length=500)
    condition: Optional[AssetCondition] = None
    photo_key: Optional[PhotoKey] = None

    @field_validator(*_BLANKABLE, mode="before")
    @classmethod
    def _blank(cls, v):
        return blank_to_none(v)

    @field_validator("acquired_on")
    @classmethod
    def _past(cls, v):
        return _not_future(v)


class ItemCreate(ItemFields):
    name: Name
    kind: ItemKind
    category: Short
    unit: Unit
    # Stock already on the shelf when the item is first entered
    opening_quantity: QtyOrZero = Decimal(0)
    opening_unit_cost: Optional[MoneyInOrZero] = None

    @model_validator(mode="after")
    def _asset_defaults(self):
        if self.kind == ItemKind.ASSET and self.condition is None:
            self.condition = AssetCondition.GOOD
        return self


class ItemUpdate(ItemFields):
    """Everything but the quantity - stock only changes through movements."""
    name: Optional[Name] = None
    is_active: Optional[bool] = None


class ItemOut(BaseModel):
    id: int
    name: str
    kind: ItemKind
    category: str
    unit: str
    quantity: Decimal
    reorder_level: Optional[Decimal] = None
    avg_unit_cost: Decimal
    location: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool
    material: Optional[str] = None
    weight_grams: Optional[Decimal] = None
    estimated_value: Optional[MoneyOut] = None
    acquired_on: Optional[date] = None
    identification: Optional[str] = None
    condition: Optional[AssetCondition] = None
    has_photo: bool = False
    last_verified_on: Optional[date] = None
    low_stock: bool = False
    stock_value: MoneyOut = Decimal(0)
    model_config = ConfigDict(from_attributes=True)


# ---- movements ----------------------------------------------------------------------------
class _MovementBase(BaseModel):
    item_id: int = Field(ge=1)
    movement_date: date
    notes: Optional[str] = Field(default=None, max_length=500)

    @field_validator("notes", mode="before")
    @classmethod
    def _blank(cls, v):
        return blank_to_none(v)

    @field_validator("movement_date")
    @classmethod
    def _past(cls, v):
        return _not_future(v)


class PurchaseIn(_MovementBase):
    quantity: Qty
    total_cost: MoneyIn
    vendor: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=255)]
    payment_mode: PaymentMode
    expense_category: Optional[ExpenseCategory] = None  # default: by item kind
    bill_key: Optional[BillKey] = None
    # No festival here: stock bought is costed to a festival when it is *used*
    # for it (UsageIn.festival_id), so tagging the purchase too would count it twice.

    @field_validator("bill_key", mode="before")
    @classmethod
    def _blank_bill(cls, v):
        return blank_to_none(v)


class DonationInIn(_MovementBase):
    quantity: Qty
    donor_name: Name
    donor_phone: Optional[Phone] = None
    donor_address: Optional[str] = Field(default=None, max_length=300)
    # The temple's own estimate, for its records (optional - flowers, small items)
    estimated_value: Optional[MoneyInOrZero] = None

    @field_validator("donor_phone", "donor_address", mode="before")
    @classmethod
    def _blank_donor(cls, v):
        return blank_to_none(v)


class UsageIn(_MovementBase):
    quantity: Qty
    pooja_id: Optional[int] = Field(default=None, ge=1)
    festival_id: Optional[int] = Field(default=None, ge=1)


class AdjustmentIn(_MovementBase):
    """A stock-take: the quantity actually counted on the shelf."""
    counted_quantity: QtyOrZero
    reason: Reason


class WriteOffIn(_MovementBase):
    quantity: Qty
    reason: Reason


class MovementOut(BaseModel):
    id: int
    item_id: int
    item_name: Optional[str] = None
    unit: Optional[str] = None
    type: MovementType
    quantity: Decimal
    balance_after: Decimal
    unit_cost: Optional[Decimal] = None
    total_value: Optional[MoneyOut] = None
    movement_date: date
    notes: Optional[str] = None
    expense_id: Optional[UUID] = None
    expense_status: Optional[ExpenseStatus] = None
    vendor: Optional[str] = None
    donor_name: Optional[str] = None
    donor_phone: Optional[str] = None
    receipt_number: Optional[str] = None
    pooja_id: Optional[int] = None
    pooja_name: Optional[str] = None
    festival_id: Optional[int] = None
    festival_name: Optional[str] = None
    created_by_name: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---- valuables verification ---------------------------------------------------------------
class VerificationIn(BaseModel):
    verified_on: date
    condition: AssetCondition
    weight_grams: Optional[Grams] = None
    notes: Optional[str] = Field(default=None, max_length=500)

    @field_validator("notes", mode="before")
    @classmethod
    def _blank(cls, v):
        return blank_to_none(v)

    @field_validator("verified_on")
    @classmethod
    def _past(cls, v):
        return _not_future(v)


class VerificationOut(BaseModel):
    id: int
    item_id: int
    verified_on: date
    condition: AssetCondition
    weight_grams: Optional[Decimal] = None
    notes: Optional[str] = None
    verified_by_name: Optional[str] = None
    # Set when the weighed weight differs from the register by more than 0.5%
    weight_mismatch: bool = False
    model_config = ConfigDict(from_attributes=True)


# ---- reports --------------------------------------------------------------------------------
class FestivalCostLine(BaseModel):
    item_name: str
    unit: str
    quantity: Decimal
    value: MoneyOut


class FestivalCost(BaseModel):
    festival_id: int
    festival_name: str
    festival_date: Optional[date] = None
    stock_used_value: MoneyOut
    expenses_total: MoneyOut
    total_cost: MoneyOut
    items: List[FestivalCostLine]


class InventorySummary(BaseModel):
    consumables: int
    valuables: int
    low_stock: int
    stock_value: MoneyOut          # consumables at average cost
    valuables_value: MoneyOut      # sum of estimated values
    valuables_unverified: int      # not verified in the current financial year (Apr-Mar)
