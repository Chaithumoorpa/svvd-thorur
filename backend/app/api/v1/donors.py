from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.pagination import PageParams, page_params, paginate, set_total
from app.core.rbac import Permission, has_permission
from app.models.user import User
from app.repositories.donor_repo import DonorRepository
from app.repositories.temple_repo import TempleRepository
from app.schemas.donor import (
    DonationCreate, DonationOut, DonationUpdate, DonorCreate, DonorOut, DonorUpdate, DonationType,
)
from app.services.donation_receipt_service import DonationReceiptService
from app.services.donor_service import DonationService, DonorService, donor_to_out
from app.utils.dependencies import AuditContext, get_audit, get_db, require_permission

router = APIRouter(tags=["Donors & Donations"])

_read_donors = require_permission(Permission.DONORS_READ)
_write_donors = require_permission(Permission.DONORS_WRITE)
_read_donations = require_permission(Permission.DONATIONS_READ)
_write_donations = require_permission(Permission.DONATIONS_WRITE)


def get_donor_service(db: Session = Depends(get_db)) -> DonorService:
    return DonorService(DonorRepository(db))


def get_donation_service(db: Session = Depends(get_db)) -> DonationService:
    return DonationService(db)


def _donation_out(donation) -> DonationOut:
    out = DonationOut.model_validate(donation)
    out.donor_name = donation.donor.name if donation.donor else None
    return out


# ------------------------------------------------------------------------- donors
@router.get("/donors/", response_model=List[DonorOut])
def list_donors(
    response: Response,
    search: Optional[str] = Query(None, max_length=100),
    service: DonorService = Depends(get_donor_service),
    params: PageParams = Depends(page_params),
    user: User = Depends(_read_donors),
):
    """Private donor directory (TRUSTEE and above). PAN is masked for read-only roles."""
    rows, total = paginate(service.query_donors(search), params)
    set_total(response, total)
    reveal = has_permission(user.roles, Permission.DONORS_WRITE)
    return [donor_to_out(row, reveal) for row in rows]


@router.get("/donors/{donor_id}", response_model=DonorOut)
def get_donor(
    donor_id: int,
    service: DonorService = Depends(get_donor_service),
    user: User = Depends(_read_donors),
):
    return donor_to_out(service.get_donor_row(donor_id), has_permission(user.roles, Permission.DONORS_WRITE))


@router.post("/donors/", response_model=DonorOut, status_code=201)
def create_donor(
    payload: DonorCreate,
    service: DonorService = Depends(get_donor_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_write_donors),
):
    donor = service.create_donor(payload)
    audit.log("CREATE", "donor", donor.id, f"Added donor {donor.name}")
    return donor_to_out(service.get_donor_row(donor.id), True)


@router.put("/donors/{donor_id}", response_model=DonorOut)
def update_donor(
    donor_id: int,
    payload: DonorUpdate,
    service: DonorService = Depends(get_donor_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_write_donors),
):
    donor = service.update_donor(donor_id, payload.model_dump(exclude_unset=True))
    audit.log("UPDATE", "donor", donor_id, f"Updated donor {donor.name}",
              {"fields": sorted(payload.model_dump(exclude_unset=True).keys())})
    return donor_to_out(service.get_donor_row(donor_id), True)


@router.delete("/donors/{donor_id}", response_model=DonorOut)
def delete_donor(
    donor_id: int,
    service: DonorService = Depends(get_donor_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_write_donors),
):
    """Soft delete: donation history is kept."""
    donor = service.delete_donor(donor_id)
    audit.log("DELETE", "donor", donor_id, f"Deactivated donor {donor.name}")
    return donor_to_out(service.get_donor_row(donor_id), True)


# ---------------------------------------------------------------------- donations
@router.get("/donations/", response_model=List[DonationOut])
def list_donations(
    response: Response,
    donor_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    donation_type: Optional[DonationType] = None,
    service: DonationService = Depends(get_donation_service),
    params: PageParams = Depends(page_params),
    _: User = Depends(_read_donations),
):
    query = service.query(donor_id, start_date, end_date, donation_type.value if donation_type else None)
    items, total = paginate(query, params)
    set_total(response, total)
    return [_donation_out(d) for d in items]


@router.post("/donations/", response_model=DonationOut, status_code=201)
def create_donation(
    payload: DonationCreate,
    service: DonationService = Depends(get_donation_service),
    audit: AuditContext = Depends(get_audit),
    user: User = Depends(_write_donations),
):
    donation = service.create(payload, user.id)
    audit.log("CREATE", "donation", donation.id, f"Recorded donation of Rs. {donation.amount} from donor #{donation.donor_id}",
              {"amount": donation.amount, "type": donation.donation_type, "mode": donation.payment_mode})
    return _donation_out(donation)


@router.put("/donations/{donation_id}", response_model=DonationOut)
def update_donation(
    donation_id: int,
    payload: DonationUpdate,
    service: DonationService = Depends(get_donation_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_write_donations),
):
    donation = service.update(donation_id, payload)
    audit.log("UPDATE", "donation", donation_id, f"Updated donation #{donation_id}",
              payload.model_dump(exclude_unset=True))
    return _donation_out(donation)


@router.post("/donations/{donation_id}/receipt", response_model=DonationOut)
def generate_receipt(
    donation_id: int,
    service: DonationService = Depends(get_donation_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_write_donations),
):
    """Issue (or return the already issued) receipt number for a donation."""
    donation = service.issue_receipt(donation_id)
    audit.log("RECEIPT", "donation", donation_id, f"Issued receipt {donation.receipt_number}")
    return _donation_out(donation)


@router.get("/donations/{donation_id}/receipt")
def download_receipt(
    donation_id: int,
    service: DonationService = Depends(get_donation_service),
    db: Session = Depends(get_db),
    _: User = Depends(_read_donations),
):
    """Receipt PDF. Authenticated (TRUSTEE+): receipts contain donor personal data."""
    from fastapi import HTTPException

    donation = service.get(donation_id)
    if not donation.receipt_number:
        raise HTTPException(status_code=400, detail="Receipt has not been generated yet")
    pdf = DonationReceiptService.generate_receipt_pdf(donation, TempleRepository(db).get_active())
    service.archive_receipt(donation, pdf)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Receipt_{donation.receipt_number}.pdf"'},
    )
