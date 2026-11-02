"""Temple inventory: items, stock movements, valuables register, festival costs."""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.core.pagination import PageParams, page_params, set_total
from app.core.rbac import Permission, has_permission
from app.models.inventory import ItemKind, MovementType
from app.models.user import User
from app.repositories.temple_repo import TempleRepository
from app.schemas.inventory import (
    AdjustmentIn, DonationInIn, FestivalCost, InventorySummary, ItemCreate, ItemOut, ItemUpdate, MovementOut,
    PurchaseIn, UsageIn, VerificationIn, VerificationOut, WriteOffIn,
)
from app.schemas.upload import UploadUrlRequest, UploadUrlResponse
from app.services.inkind_receipt_service import generate_inkind_receipt_pdf
from app.services.inventory_service import InventoryService, _fmt_qty
from app.utils.dependencies import AuditContext, get_audit, get_db, require_permission

router = APIRouter()

_read = require_permission(Permission.INVENTORY_READ)
_write = require_permission(Permission.INVENTORY_WRITE)
_manage = require_permission(Permission.INVENTORY_MANAGE)


def get_inventory_service(db: Session = Depends(get_db)) -> InventoryService:
    return InventoryService(db)


# ---- items --------------------------------------------------------------------------------
@router.get("/summary", response_model=InventorySummary, dependencies=[Depends(_read)])
def summary(service: InventoryService = Depends(get_inventory_service)):
    return service.summary()


@router.get("/items", response_model=List[ItemOut], dependencies=[Depends(_read)])
def list_items(kind: Optional[ItemKind] = None, category: Optional[str] = Query(None, max_length=60),
               low_stock: bool = False, q: Optional[str] = Query(None, max_length=100),
               include_inactive: bool = False, service: InventoryService = Depends(get_inventory_service)):
    return service.list_items(kind, category, low_stock, q, include_inactive)


@router.get("/categories", response_model=List[str], dependencies=[Depends(_read)])
def categories(service: InventoryService = Depends(get_inventory_service)):
    return service.categories()


@router.post("/items", response_model=ItemOut, status_code=201)
def create_item(payload: ItemCreate, service: InventoryService = Depends(get_inventory_service),
                audit: AuditContext = Depends(get_audit), user: User = Depends(_manage)):
    item = service.create_item(payload, user)
    audit.log("CREATE", "inventory_item", item.id, f"Added {item.kind.value.lower()} '{item.name}'",
              {"category": item.category, "unit": item.unit, "opening_quantity": payload.opening_quantity,
               "weight_grams": item.weight_grams, "estimated_value": item.estimated_value})
    return service.item_out(item)


@router.get("/items/{item_id}", response_model=ItemOut, dependencies=[Depends(_read)])
def get_item(item_id: int, service: InventoryService = Depends(get_inventory_service)):
    return service.item_out(service.get_item(item_id))


@router.patch("/items/{item_id}", response_model=ItemOut)
def update_item(item_id: int, payload: ItemUpdate, service: InventoryService = Depends(get_inventory_service),
                audit: AuditContext = Depends(get_audit), _: User = Depends(_manage)):
    item, changes = service.update_item(item_id, payload)
    if changes:
        audit.log("UPDATE", "inventory_item", item.id, f"Updated '{item.name}'", changes)
    return service.item_out(item)


@router.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int, service: InventoryService = Depends(get_inventory_service),
                audit: AuditContext = Depends(get_audit), _: User = Depends(_manage)):
    item = service.delete_item(item_id)
    audit.log("DELETE", "inventory_item", item_id, f"Deleted '{item.name}' (entered by mistake, no history)")
    return Response(status_code=204)


@router.post("/items/photo-upload-url", response_model=UploadUrlResponse, dependencies=[Depends(_manage)])
def photo_upload_url(payload: UploadUrlRequest, service: InventoryService = Depends(get_inventory_service)):
    """Presigned upload for a valuable's photo - private, viewed via /items/{id}/photo."""
    return service.photo_upload(payload.content_type)


@router.get("/items/{item_id}/photo", dependencies=[Depends(_read)])
def photo_link(item_id: int, service: InventoryService = Depends(get_inventory_service)):
    """A 5-minute private link to the item's photo."""
    return {"url": service.photo_link(item_id)}


# ---- movements ----------------------------------------------------------------------------
@router.get("/movements", response_model=List[MovementOut], dependencies=[Depends(_read)])
def list_movements(response: Response, item_id: Optional[int] = None, type: Optional[MovementType] = None,
                   festival_id: Optional[int] = None, pooja_id: Optional[int] = None,
                   start_date: Optional[date] = None, end_date: Optional[date] = None,
                   params: PageParams = Depends(page_params),
                   service: InventoryService = Depends(get_inventory_service)):
    items, total = service.list_movements(params, item_id=item_id, type=type, festival_id=festival_id,
                                          pooja_id=pooja_id, start=start_date, end=end_date)
    set_total(response, total)
    return items


def _one(service: InventoryService, movement) -> MovementOut:
    items, _ = service.list_movements(PageParams(1, 1), movement_id=movement.id)
    return items[0]


@router.post("/purchases", response_model=MovementOut, status_code=201)
def purchase(payload: PurchaseIn, service: InventoryService = Depends(get_inventory_service),
             audit: AuditContext = Depends(get_audit), user: User = Depends(_write)):
    """Stock in + the matching expense (pending approval unless entered by an admin)."""
    can_approve = has_permission(user.roles, Permission.FINANCE_WRITE)
    movement = service.purchase(payload, user, can_approve)
    item = movement.item
    audit.log("PURCHASE", "inventory_item", item.id,
              f"Bought {_fmt_qty(payload.quantity)} {item.unit} {item.name} for Rs. {payload.total_cost}",
              {"quantity": payload.quantity, "total_cost": payload.total_cost, "vendor": payload.vendor,
               "expense_id": movement.expense_id})
    return _one(service, movement)


@router.post("/donations-in", response_model=MovementOut, status_code=201)
def donation_in(payload: DonationInIn, service: InventoryService = Depends(get_inventory_service),
                audit: AuditContext = Depends(get_audit), user: User = Depends(_write)):
    movement = service.donation_in(payload, user)
    item = movement.item
    audit.log("DONATION_IN", "inventory_item", item.id,
              f"Received {_fmt_qty(payload.quantity)} {item.unit} {item.name} from {payload.donor_name} "
              f"({movement.receipt_number})", {"quantity": payload.quantity, "receipt": movement.receipt_number})
    return _one(service, movement)


@router.post("/usage", response_model=MovementOut, status_code=201)
def usage(payload: UsageIn, service: InventoryService = Depends(get_inventory_service),
          audit: AuditContext = Depends(get_audit), user: User = Depends(_write)):
    movement = service.usage(payload, user)
    item = movement.item
    audit.log("USAGE", "inventory_item", item.id, f"Used {_fmt_qty(payload.quantity)} {item.unit} {item.name}",
              {"quantity": payload.quantity, "pooja_id": payload.pooja_id, "festival_id": payload.festival_id})
    return _one(service, movement)


@router.post("/adjustments", response_model=MovementOut, status_code=201)
def adjustment(payload: AdjustmentIn, service: InventoryService = Depends(get_inventory_service),
               audit: AuditContext = Depends(get_audit), user: User = Depends(_manage)):
    movement = service.adjustment(payload, user)
    item = movement.item
    audit.log("ADJUST", "inventory_item", item.id,
              f"Stock count of {item.name}: {_fmt_qty(movement.quantity)} {item.unit} ({payload.reason})",
              {"counted": payload.counted_quantity, "change": movement.quantity, "reason": payload.reason})
    return _one(service, movement)


@router.post("/write-offs", response_model=MovementOut, status_code=201)
def write_off(payload: WriteOffIn, service: InventoryService = Depends(get_inventory_service),
              audit: AuditContext = Depends(get_audit), user: User = Depends(_manage)):
    movement = service.write_off(payload, user)
    item = movement.item
    audit.log("WRITE_OFF", "inventory_item", item.id,
              f"Wrote off {_fmt_qty(payload.quantity)} {item.unit} {item.name} ({payload.reason})",
              {"quantity": payload.quantity, "reason": payload.reason})
    return _one(service, movement)


@router.get("/movements/{movement_id}/receipt", dependencies=[Depends(_read)])
def inkind_receipt(movement_id: int, service: InventoryService = Depends(get_inventory_service),
                   db: Session = Depends(get_db)):
    """Printable acknowledgement for a donation in kind."""
    movement = service.get_movement(movement_id)
    if movement.type != MovementType.DONATION_IN or not movement.receipt_number:
        raise HTTPException(status_code=400, detail="Only a donation in kind has an acknowledgement")
    received_by = db.get(User, movement.created_by).username if movement.created_by else None
    pdf = generate_inkind_receipt_pdf(movement, movement.item, TempleRepository(db).get_active(), received_by)
    return Response(content=pdf, media_type="application/pdf", headers={
        "Content-Disposition": f'inline; filename="{movement.receipt_number}.pdf"'})


# ---- valuables ----------------------------------------------------------------------------
@router.post("/items/{item_id}/verifications", response_model=VerificationOut, status_code=201)
def verify(item_id: int, payload: VerificationIn, service: InventoryService = Depends(get_inventory_service),
           audit: AuditContext = Depends(get_audit), user: User = Depends(_manage)):
    out = service.verify(item_id, payload, user)
    item = service.get_item(item_id)
    audit.log("VERIFY", "inventory_item", item_id,
              f"Verified '{item.name}': {payload.condition.value.lower().replace('_', ' ')}"
              + (" - WEIGHT DIFFERS FROM REGISTER" if out.weight_mismatch else ""),
              {"weight_grams": payload.weight_grams, "condition": payload.condition,
               "weight_mismatch": out.weight_mismatch})
    return out


@router.get("/items/{item_id}/verifications", response_model=List[VerificationOut], dependencies=[Depends(_read)])
def verifications(item_id: int, service: InventoryService = Depends(get_inventory_service)):
    return service.verifications(item_id)


# ---- reports ------------------------------------------------------------------------------
@router.get("/festival-costs", response_model=List[FestivalCost], dependencies=[Depends(_read)])
def festival_costs(festival_id: Optional[int] = None, service: InventoryService = Depends(get_inventory_service)):
    """What each festival cost: stock used (at average cost) + expenses tagged to it."""
    return service.festival_costs(festival_id)
