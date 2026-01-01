from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from app.utils.dependencies import get_db, require_admin, require_trustee
from app.repositories.donor_repo import DonorRepository
from app.services.donor_service import DonorService
from app.schemas.donor import DonorOut, DonorCreate, DonorUpdate
from app.models.user import User
from app.services.donation_receipt_service import DonationReceiptService
from fastapi.responses import Response
from datetime import datetime

router = APIRouter(prefix="/donors", tags=["Donors"])
logger = logging.getLogger(__name__)


def get_donor_service(
    db: Session = Depends(get_db),
) -> DonorService:
    repo = DonorRepository(db)
    return DonorService(repo)


@router.get("/", response_model=List[DonorOut])
def list_donors(
    service: DonorService = Depends(get_donor_service),
    current_user: User = Depends(require_trustee),  # TRUSTEE can view donors
):
    """List all donors. Requires at least TRUSTEE role."""
    logger.info(
        f"Donors GET (list): user={current_user.username}, "
        f"roles={current_user.roles}"
    )
    return service.list_donors()


@router.get("/{donor_id}", response_model=DonorOut)
def get_donor(
    donor_id: int,
    service: DonorService = Depends(get_donor_service),
    current_user: User = Depends(require_trustee),  # TRUSTEE can view donors
):
    """Get donor by ID. Requires at least TRUSTEE role."""
    logger.info(
        f"Donors GET (single): user={current_user.username}, "
        f"roles={current_user.roles}, donor_id={donor_id}"
    )
    donor = service.get_donor(donor_id)
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    return donor


@router.post("/", response_model=DonorOut)
def create_donor(
    payload: DonorCreate,
    service: DonorService = Depends(get_donor_service),
    current_user: User = Depends(require_admin),  # ADMIN or SUPER_ADMIN only
):
    """Create a new donor. Requires ADMIN or SUPER_ADMIN role."""
    logger.info(
        f"Donors POST: user={current_user.username}, "
        f"roles={current_user.roles}, donor_name={payload.name}"
    )
    result = service.create_donor(payload)
    logger.info(f"Donor created: id={result.id}, name={result.name}")
    return result


@router.put("/{donor_id}", response_model=DonorOut)
def update_donor(
    donor_id: int,
    payload: DonorUpdate,
    service: DonorService = Depends(get_donor_service),
    current_user: User = Depends(require_admin),  # ADMIN or SUPER_ADMIN only
):
    """Update a donor. Requires ADMIN or SUPER_ADMIN role."""
    logger.info(
        f"Donors PUT: user={current_user.username}, "
        f"roles={current_user.roles}, donor_id={donor_id}"
    )
    result = service.update_donor(donor_id, payload.dict(exclude_unset=True))
    logger.info(f"Donor updated: id={donor_id}")
    return result


@router.delete("/{donor_id}", response_model=DonorOut)
def delete_donor(
    donor_id: int,
    service: DonorService = Depends(get_donor_service),
    current_user: User = Depends(require_admin),  # ADMIN or SUPER_ADMIN only
):
    """Delete a donor. Requires ADMIN or SUPER_ADMIN role."""
    logger.info(
        f"Donors DELETE: user={current_user.username}, "
        f"roles={current_user.roles}, donor_id={donor_id}"
    )
    result = service.delete_donor(donor_id)
    logger.info(f"Donor deleted: id={donor_id}")
    return result


@router.post("/{donor_id}/generate-receipt", dependencies=[Depends(require_admin)])
def generate_receipt(
    donor_id: int,
    db: Session = Depends(get_db),
    service: DonorService = Depends(get_donor_service),
):
    """
    Generate a receipt for a donation (ADMIN only).
    Assigns a receipt number if not present.
    """
    donor = service.get_donor(donor_id)
    if not donor:
        raise HTTPException(status_code=404, detail="Donation not found")

    if not donor.receipt_number:
        donor.receipt_number = DonationReceiptService.generate_receipt_number(db)
        donor.receipt_generated_at = datetime.now()
        db.commit()
        db.refresh(donor)
    
    return {"message": "Receipt generated successfully", "receipt_number": donor.receipt_number}


@router.get("/{donor_id}/receipt")
def get_receipt(
    donor_id: int,
    service: DonorService = Depends(get_donor_service),
):
    """
    Download donation receipt PDF (Public access permitted by ID).
    """
    donor = service.get_donor(donor_id)
    if not donor:
        raise HTTPException(status_code=404, detail="Donation not found")
        
    if not donor.receipt_number:
         raise HTTPException(status_code=400, detail="Receipt has not been generated yet. Please contact admin.")

    pdf_content = DonationReceiptService.generate_receipt_pdf(donor)
    
    filename = f"Receipt_{donor.receipt_number}.pdf"
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
