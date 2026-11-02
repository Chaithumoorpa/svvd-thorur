"""Inventory: items, stock movements, valuables verification and festival costs.

Stock never changes except through a movement, and every movement records
the balance it left behind, so an item's history always adds up to its
current quantity. Costs use a weighted average: each purchase (or valued
donation) re-averages the unit cost, and stock used is valued at the
average at the time - which is how a festival's cost is worked out.
"""
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.pagination import PageParams
from app.models.festival import Festival
from app.models.finance import ExpenseCategory, ExpenseStatus, ExpenseTransaction
from app.models.inventory import (
    AssetVerification, InventoryItem, ItemKind, MovementType, StockMovement,
)
from app.models.pooja import Pooja
from app.models.user import User
from app.schemas.finance import ExpenseTransactionCreate
from app.schemas.inventory import (
    INVENTORY_PHOTO_PREFIX, AdjustmentIn, DonationInIn, FestivalCost, FestivalCostLine, InventorySummary,
    ItemCreate, ItemOut, ItemUpdate, MovementOut, PurchaseIn, UsageIn, VerificationIn, VerificationOut,
    WriteOffIn,
)
from app.services.expense_service import ExpenseService
from app.services.storage_service import StorageService

Q3 = Decimal("0.001")
Q4 = Decimal("0.0001")
Q2 = Decimal("0.01")
WEIGHT_TOLERANCE = Decimal("0.005")  # 0.5%: a gold/silver item weighing off by more is flagged


def _q(value, places=Q3) -> Decimal:
    return Decimal(value).quantize(places, rounding=ROUND_HALF_UP)


def _fmt_qty(value: Decimal) -> str:
    """2.500 -> '2.5', 3.000 -> '3'."""
    text = f"{_q(value):f}".rstrip("0").rstrip(".")
    return text or "0"


def financial_year_start(today: Optional[date] = None) -> date:
    today = today or date.today()
    return date(today.year if today.month >= 4 else today.year - 1, 4, 1)


class InventoryService:
    def __init__(self, db: Session, storage: Optional[StorageService] = None):
        self.db = db
        self.storage = storage or StorageService()

    # ---- items -----------------------------------------------------------------------
    @staticmethod
    def item_out(item: InventoryItem) -> ItemOut:
        out = ItemOut.model_validate(item)
        out.has_photo = bool(item.photo_key)
        if item.kind == ItemKind.CONSUMABLE:
            out.low_stock = item.reorder_level is not None and item.quantity <= item.reorder_level
            out.stock_value = _q(Decimal(item.quantity) * Decimal(item.avg_unit_cost), Q2)
        else:
            out.stock_value = Decimal(item.estimated_value or 0)
        return out

    def get_item(self, item_id: int) -> InventoryItem:
        item = self.db.get(InventoryItem, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return item

    def list_items(self, kind: Optional[ItemKind] = None, category: Optional[str] = None,
                   low_stock: bool = False, search: Optional[str] = None,
                   include_inactive: bool = False) -> List[ItemOut]:
        query = self.db.query(InventoryItem)
        if not include_inactive:
            query = query.filter(InventoryItem.is_active.is_(True))
        if kind:
            query = query.filter(InventoryItem.kind == kind)
        if category:
            query = query.filter(InventoryItem.category == category)
        if low_stock:
            query = query.filter(InventoryItem.kind == ItemKind.CONSUMABLE,
                                 InventoryItem.reorder_level.isnot(None),
                                 InventoryItem.quantity <= InventoryItem.reorder_level)
        if search:
            query = query.filter(InventoryItem.name.ilike(f"%{search.strip()}%"))
        return [self.item_out(i) for i in query.order_by(InventoryItem.category, InventoryItem.name, InventoryItem.id)]

    def categories(self) -> List[str]:
        return [c for (c,) in self.db.query(InventoryItem.category).distinct().order_by(InventoryItem.category)]

    def create_item(self, data: ItemCreate, user: User) -> InventoryItem:
        self._unique_name(data.name, data.kind)
        fields = data.model_dump(exclude={"opening_quantity", "opening_unit_cost"})
        item = InventoryItem(**fields, quantity=0, avg_unit_cost=0, created_by=user.id)
        self.db.add(item)
        self.db.flush()
        if data.opening_quantity > 0:
            cost = Decimal(data.opening_unit_cost or 0)
            item.avg_unit_cost = _q(cost, Q4)
            self._move(item, MovementType.ADJUSTMENT, data.opening_quantity, date.today(), user,
                       unit_cost=cost, notes="Opening stock")
        self.db.commit()
        self.db.refresh(item)
        return item

    def update_item(self, item_id: int, data: ItemUpdate) -> Tuple[InventoryItem, Dict]:
        item = self.get_item(item_id)
        fields = data.model_dump(exclude_unset=True)
        if fields.get("name") and fields["name"].lower() != item.name.lower():
            self._unique_name(fields["name"], item.kind)
        changes = {}
        for key, value in fields.items():
            if key in ("name", "category", "unit") and value is None:
                continue  # required fields can't be blanked
            if value != getattr(item, key):
                changes[key] = {"from": _plain(getattr(item, key)), "to": _plain(value)}
                setattr(item, key, value)
        if changes:
            self.db.commit()
            self.db.refresh(item)
        return item, changes

    def delete_item(self, item_id: int) -> InventoryItem:
        """Only an item entered by mistake (no history at all) can be deleted;
        anything with movements is deactivated instead, keeping its records."""
        item = self.get_item(item_id)
        if self.db.query(StockMovement.id).filter(StockMovement.item_id == item.id).first():
            raise HTTPException(status_code=409,
                                detail="This item has stock history - deactivate it instead of deleting")
        self.db.delete(item)
        self.db.commit()
        return item

    def photo_upload(self, content_type: str) -> dict:
        return self.storage.create_upload(content_type, key_prefix=INVENTORY_PHOTO_PREFIX)

    def photo_link(self, item_id: int) -> str:
        item = self.get_item(item_id)
        if not item.photo_key:
            raise HTTPException(status_code=404, detail="No photo for this item")
        if not self.storage.enabled:
            raise HTTPException(status_code=503, detail="File storage is not configured")
        return self.storage.presigned_get(item.photo_key, expires_in=300)

    # ---- movements -------------------------------------------------------------------
    def purchase(self, data: PurchaseIn, user: User, can_approve: bool) -> StockMovement:
        """Stock in, and the matching expense (approved at once for an admin,
        pending approval otherwise - the goods are on the shelf either way)."""
        item = self._active(data.item_id)
        category = data.expense_category or (
            ExpenseCategory.ASSETS if item.kind == ItemKind.ASSET else ExpenseCategory.POOJA_SUPPLIES)
        description = f"Stock purchase: {_fmt_qty(data.quantity)} {item.unit} {item.name}"[:255]
        expense = ExpenseService(self.db, self.storage).build(ExpenseTransactionCreate(
            category=category, description=description, amount=data.total_cost, payment_mode=data.payment_mode,
            paid_to=data.vendor, expense_date=data.movement_date, notes=data.notes, bill_key=data.bill_key,
        ), user, can_approve)
        self.db.flush()
        unit_cost = Decimal(data.total_cost) / Decimal(data.quantity)
        self._reaverage(item, data.quantity, Decimal(data.total_cost))
        movement = self._move(item, MovementType.PURCHASE, data.quantity, data.movement_date, user,
                              unit_cost=unit_cost, notes=data.notes, expense_id=expense.id, vendor=data.vendor)
        self.db.commit()
        return movement

    def donation_in(self, data: DonationInIn, user: User) -> StockMovement:
        item = self._active(data.item_id)
        value = Decimal(data.estimated_value or 0)
        if value:
            self._reaverage(item, data.quantity, value)
        for attempt in range(3):
            receipt = self._next_receipt_number(data.movement_date.year, attempt)
            movement = self._move(
                item, MovementType.DONATION_IN, data.quantity, data.movement_date, user,
                unit_cost=value / Decimal(data.quantity) if value else None, notes=data.notes,
                donor_name=data.donor_name, donor_phone=data.donor_phone, donor_address=data.donor_address,
                receipt_number=receipt,
            )
            try:
                self.db.commit()
                return movement
            except IntegrityError:  # two receipts numbered at the same moment - take the next number
                self.db.rollback()
                item = self._active(data.item_id)
                if value:
                    self._reaverage(item, data.quantity, value)
        raise HTTPException(status_code=409, detail="Could not number the receipt, please try again")

    def usage(self, data: UsageIn, user: User) -> StockMovement:
        item = self._active(data.item_id)
        if item.kind == ItemKind.ASSET:
            raise HTTPException(status_code=409, detail="Valuables aren't used up - record a write-off "
                                                        "if one is lost or damaged")
        if data.pooja_id and not self.db.get(Pooja, data.pooja_id):
            raise HTTPException(status_code=422, detail="That seva doesn't exist")
        if data.festival_id and not self.db.get(Festival, data.festival_id):
            raise HTTPException(status_code=422, detail="That festival doesn't exist")
        self._enough(item, data.quantity)
        movement = self._move(item, MovementType.USAGE, -Decimal(data.quantity), data.movement_date, user,
                              unit_cost=Decimal(item.avg_unit_cost), notes=data.notes,
                              pooja_id=data.pooja_id, festival_id=data.festival_id)
        self.db.commit()
        return movement

    def adjustment(self, data: AdjustmentIn, user: User) -> StockMovement:
        item = self._active(data.item_id)
        delta = Decimal(data.counted_quantity) - Decimal(item.quantity)
        if delta == 0:
            raise HTTPException(status_code=409, detail="The count already matches the stock - nothing to adjust")
        notes = data.reason if not data.notes else f"{data.reason} - {data.notes}"
        movement = self._move(item, MovementType.ADJUSTMENT, delta, data.movement_date, user,
                              unit_cost=Decimal(item.avg_unit_cost), notes=notes[:500])
        self.db.commit()
        return movement

    def write_off(self, data: WriteOffIn, user: User) -> StockMovement:
        item = self._active(data.item_id)
        self._enough(item, data.quantity)
        notes = data.reason if not data.notes else f"{data.reason} - {data.notes}"
        movement = self._move(item, MovementType.WRITE_OFF, -Decimal(data.quantity), data.movement_date, user,
                              unit_cost=Decimal(item.avg_unit_cost), notes=notes[:500])
        if item.kind == ItemKind.ASSET and item.quantity == 0:
            item.is_active = False
        self.db.commit()
        return movement

    def get_movement(self, movement_id: int) -> StockMovement:
        movement = self.db.get(StockMovement, movement_id)
        if not movement:
            raise HTTPException(status_code=404, detail="Stock entry not found")
        return movement

    def list_movements(self, params: PageParams, *, movement_id: Optional[int] = None, item_id: Optional[int] = None,
                       type: Optional[MovementType] = None, festival_id: Optional[int] = None,
                       pooja_id: Optional[int] = None, start: Optional[date] = None,
                       end: Optional[date] = None) -> Tuple[List[MovementOut], int]:
        query = (
            self.db.query(StockMovement, InventoryItem.name, InventoryItem.unit, User.username, Pooja.name,
                          Festival.name, ExpenseTransaction.status)
            .join(InventoryItem, InventoryItem.id == StockMovement.item_id)
            .outerjoin(User, User.id == StockMovement.created_by)
            .outerjoin(Pooja, Pooja.id == StockMovement.pooja_id)
            .outerjoin(Festival, Festival.id == StockMovement.festival_id)
            .outerjoin(ExpenseTransaction, ExpenseTransaction.id == StockMovement.expense_id)
        )
        if movement_id:
            query = query.filter(StockMovement.id == movement_id)
        if item_id:
            query = query.filter(StockMovement.item_id == item_id)
        if type:
            query = query.filter(StockMovement.type == type)
        if festival_id:
            query = query.filter(StockMovement.festival_id == festival_id)
        if pooja_id:
            query = query.filter(StockMovement.pooja_id == pooja_id)
        if start:
            query = query.filter(StockMovement.movement_date >= start)
        if end:
            query = query.filter(StockMovement.movement_date <= end)
        total = query.order_by(None).count()
        rows = (query.order_by(StockMovement.movement_date.desc(), StockMovement.id.desc())
                .offset(params.offset).limit(params.page_size).all())
        out = []
        for movement, item_name, unit, username, pooja_name, festival_name, expense_status in rows:
            m = MovementOut.model_validate(movement)
            m.item_name, m.unit, m.created_by_name = item_name, unit, username
            m.pooja_name, m.festival_name, m.expense_status = pooja_name, festival_name, expense_status
            out.append(m)
        return out, total

    # ---- valuables -------------------------------------------------------------------
    def verify(self, item_id: int, data: VerificationIn, user: User) -> VerificationOut:
        item = self.get_item(item_id)
        if item.kind != ItemKind.ASSET:
            raise HTTPException(status_code=409, detail="Only valuables are verified - count stock with an adjustment")
        row = AssetVerification(item_id=item.id, verified_by=user.id, **data.model_dump())
        self.db.add(row)
        item.condition = data.condition
        if not item.last_verified_on or data.verified_on >= item.last_verified_on:
            item.last_verified_on = data.verified_on
        self.db.commit()
        self.db.refresh(row)
        return self._verification_out(row, item, user.username)

    def verifications(self, item_id: int) -> List[VerificationOut]:
        item = self.get_item(item_id)
        rows = (self.db.query(AssetVerification, User.username)
                .outerjoin(User, User.id == AssetVerification.verified_by)
                .filter(AssetVerification.item_id == item.id)
                .order_by(AssetVerification.verified_on.desc(), AssetVerification.id.desc()).all())
        return [self._verification_out(v, item, name) for v, name in rows]

    @staticmethod
    def _verification_out(row: AssetVerification, item: InventoryItem, username: Optional[str]) -> VerificationOut:
        out = VerificationOut.model_validate(row)
        out.verified_by_name = username
        if row.weight_grams and item.weight_grams:
            registered = Decimal(item.weight_grams)
            out.weight_mismatch = abs(Decimal(row.weight_grams) - registered) > registered * WEIGHT_TOLERANCE
        return out

    # ---- reports ---------------------------------------------------------------------
    def summary(self) -> InventorySummary:
        items = self.db.query(InventoryItem).filter(InventoryItem.is_active.is_(True)).all()
        consumables = [i for i in items if i.kind == ItemKind.CONSUMABLE]
        valuables = [i for i in items if i.kind == ItemKind.ASSET]
        fy_start = financial_year_start()
        return InventorySummary(
            consumables=len(consumables),
            valuables=len(valuables),
            low_stock=sum(1 for i in consumables if i.reorder_level is not None and i.quantity <= i.reorder_level),
            stock_value=_q(sum((Decimal(i.quantity) * Decimal(i.avg_unit_cost) for i in consumables), Decimal(0)), Q2),
            valuables_value=sum((Decimal(i.estimated_value or 0) for i in valuables), Decimal(0)),
            valuables_unverified=sum(1 for i in valuables if not i.last_verified_on or i.last_verified_on < fy_start),
        )

    def festival_costs(self, festival_id: Optional[int] = None) -> List[FestivalCost]:
        """Per festival: stock used (at average cost) + approved expenses tagged to
        it. Expenses that are inventory purchases are left out - their stock is
        counted when used, so counting the purchase too would double it."""
        usage = (self.db.query(StockMovement.festival_id, InventoryItem.name, InventoryItem.unit,
                               func.sum(-StockMovement.quantity), func.sum(-StockMovement.total_value))
                 .join(InventoryItem, InventoryItem.id == StockMovement.item_id)
                 .filter(StockMovement.type == MovementType.USAGE, StockMovement.festival_id.isnot(None))
                 .group_by(StockMovement.festival_id, InventoryItem.name, InventoryItem.unit))
        purchase_expenses = self.db.query(StockMovement.expense_id).filter(StockMovement.expense_id.isnot(None))
        expenses = (self.db.query(ExpenseTransaction.festival_id, func.sum(ExpenseTransaction.amount))
                    .filter(ExpenseTransaction.festival_id.isnot(None),
                            ExpenseTransaction.status == ExpenseStatus.APPROVED,
                            ExpenseTransaction.id.notin_(purchase_expenses))
                    .group_by(ExpenseTransaction.festival_id))
        if festival_id:
            usage = usage.filter(StockMovement.festival_id == festival_id)
            expenses = expenses.filter(ExpenseTransaction.festival_id == festival_id)

        lines: Dict[int, List[FestivalCostLine]] = {}
        for fid, name, unit, qty, value in usage:
            lines.setdefault(fid, []).append(FestivalCostLine(
                item_name=name, unit=unit, quantity=_q(qty or 0), value=_q(value or 0, Q2)))
        spent = {fid: Decimal(total or 0) for fid, total in expenses}
        ids = set(lines) | set(spent)
        if not ids:
            return []
        festivals = {f.id: f for f in self.db.query(Festival).filter(Festival.id.in_(ids))}
        out = []
        for fid in ids:
            festival = festivals.get(fid)
            if not festival:
                continue
            items = sorted(lines.get(fid, []), key=lambda l: l.value, reverse=True)
            used = sum((l.value for l in items), Decimal(0))
            out.append(FestivalCost(
                festival_id=fid, festival_name=festival.name, festival_date=festival.festival_date,
                stock_used_value=used, expenses_total=spent.get(fid, Decimal(0)),
                total_cost=used + spent.get(fid, Decimal(0)), items=items,
            ))
        out.sort(key=lambda c: (c.festival_date or date.min, c.festival_id), reverse=True)
        return out

    # ---- helpers ---------------------------------------------------------------------
    def _active(self, item_id: int) -> InventoryItem:
        item = self.get_item(item_id)
        if not item.is_active:
            raise HTTPException(status_code=409, detail=f"{item.name} is deactivated - reactivate it first")
        return item

    @staticmethod
    def _enough(item: InventoryItem, quantity: Decimal) -> None:
        if Decimal(quantity) > Decimal(item.quantity):
            raise HTTPException(status_code=409,
                                detail=f"Only {_fmt_qty(item.quantity)} {item.unit} of {item.name} in stock")

    @staticmethod
    def _reaverage(item: InventoryItem, quantity: Decimal, value: Decimal) -> None:
        on_hand = max(Decimal(item.quantity), Decimal(0))
        total_qty = on_hand + Decimal(quantity)
        item.avg_unit_cost = _q((on_hand * Decimal(item.avg_unit_cost) + value) / total_qty, Q4)

    def _move(self, item: InventoryItem, type: MovementType, quantity: Decimal, when: date, user: User,
              unit_cost: Optional[Decimal] = None, **fields) -> StockMovement:
        quantity = _q(quantity)
        item.quantity = _q(Decimal(item.quantity) + quantity)
        movement = StockMovement(
            item_id=item.id, type=type, quantity=quantity, balance_after=item.quantity,
            unit_cost=_q(unit_cost, Q4) if unit_cost is not None else None,
            total_value=_q(quantity * unit_cost, Q2) if unit_cost is not None else None,
            movement_date=when, created_by=user.id, **fields,
        )
        self.db.add(movement)
        return movement

    def _next_receipt_number(self, year: int, bump: int = 0) -> str:
        prefix = f"IK-{year}-"
        count = self.db.query(func.count(StockMovement.id)) \
            .filter(StockMovement.receipt_number.like(f"{prefix}%")).scalar() or 0
        return f"{prefix}{count + 1 + bump:04d}"

    def _unique_name(self, name: str, kind: ItemKind) -> None:
        clash = self.db.query(InventoryItem.id).filter(
            func.lower(InventoryItem.name) == name.strip().lower(), InventoryItem.kind == kind,
            InventoryItem.is_active.is_(True)).first()
        if clash:
            raise HTTPException(status_code=409, detail=f"An item called '{name}' already exists")


def _plain(value):
    if isinstance(value, (Decimal, date)):
        return str(value)
    return getattr(value, "value", value)
