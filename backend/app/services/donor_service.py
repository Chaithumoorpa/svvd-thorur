import logging
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.donation import Donation
from app.models.donor import Donor
from app.models.finance import IncomeSourceType, IncomeTransaction
from app.repositories.donor_repo import DonationRepository, DonorRepository
from app.schemas.donor import (
    DonationCreate, DonationUpdate, DonorCreate, DonorOut, mask_pan,
)


def donor_to_out(row, reveal_pan: bool) -> DonorOut:
    """Map a (Donor, count, total) row to the API model, masking the PAN when required."""
    donor, count, total = row
    out = DonorOut.model_validate(donor)
    out.donation_count = int(count or 0)
    out.total_donated = Decimal(total or 0)
    if not reveal_pan:
        out.pan_number = mask_pan(out.pan_number)
    return out


class DonorService:
    def __init__(self, repository: DonorRepository):
        self.repository = repository

    def query_donors(self, search: Optional[str] = None):
        return self.repository.query_with_totals(search)

    def list_donors(self):
        return self.repository.get_all()

    def get_donor(self, donor_id: int) -> Donor:
        donor = self.repository.get_by_id(donor_id)
        if not donor:
            raise HTTPException(status_code=404, detail="Donor not found")
        return donor

    def get_donor_row(self, donor_id: int):
        row = self.repository.get_with_totals(donor_id)
        if not row:
            raise HTTPException(status_code=404, detail="Donor not found")
        return row

    def create_donor(self, data: DonorCreate) -> Donor:
        return self.repository.create(Donor(**data.model_dump()))

    def update_donor(self, donor_id: int, data: dict) -> Donor:
        donor = self.get_donor(donor_id)
        clean = {k: v for k, v in data.items() if not (k in ("name", "is_active") and v is None)}
        return self.repository.update(donor, clean)

    def delete_donor(self, donor_id: int) -> Donor:
        return self.repository.delete(self.get_donor(donor_id))


class DonationService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DonationRepository(db)
        self.donors = DonorRepository(db)

    # ---- queries -----------------------------------------------------------------
    def query(self, donor_id=None, start: Optional[date] = None, end: Optional[date] = None,
              donation_type: Optional[str] = None):
        start_dt = datetime.combine(start, time.min) if start else None
        # `end` is inclusive for the caller -> exclusive next-day boundary for the query
        end_dt = datetime.combine(end + timedelta(days=1), time.min) if end else None
        return self.repo.query(donor_id, start_dt, end_dt, donation_type)

    def get(self, donation_id: int) -> Donation:
        donation = self.repo.get_by_id(donation_id)
        if not donation:
            raise HTTPException(status_code=404, detail="Donation not found")
        return donation

    # ---- commands ----------------------------------------------------------------
    def create(self, data: DonationCreate, user_id: int) -> Donation:
        donor = self.donors.get_by_id(data.donor_id)
        if not donor or not donor.is_active:
            raise HTTPException(status_code=400, detail="Donor not found or inactive")

        donation = Donation(
            donor_id=data.donor_id,
            amount=data.amount,
            donation_type=data.donation_type.value,
            purpose=data.purpose,
            donated_on=data.donated_on or datetime.now(),
            payment_mode=data.payment_mode,
            recorded_by_id=user_id,
        )
        self.db.add(donation)
        self.db.flush()  # need the id for the ledger reference

        # Same transaction: a gift and its ledger entry are stored together or not at all.
        self.db.add(IncomeTransaction(
            source_type=IncomeSourceType.DONATION,
            reference_id=f"donation:{donation.id}",
            amount=data.amount,
            payment_mode=data.payment_mode,
            received_by=user_id,
            received_at=donation.donated_on,
            notes=f"Donation from {donor.name}",
        ))
        self.db.commit()
        return self.get(donation.id)

    def _linked_income(self, donation_id: int) -> Optional[IncomeTransaction]:
        return (
            self.db.query(IncomeTransaction)
            .filter(IncomeTransaction.reference_id == f"donation:{donation_id}")
            .first()
        )

    def update(self, donation_id: int, data: DonationUpdate) -> Donation:
        donation = self.get(donation_id)
        fields = data.model_dump(exclude_unset=True)
        if donation.receipt_number and ("amount" in fields or "donated_on" in fields):
            raise HTTPException(
                status_code=409,
                detail="A receipt was already issued; the amount and date can no longer be changed",
            )
        for key, value in fields.items():
            if value is None and key in ("amount", "donation_type", "donated_on", "payment_mode"):
                continue
            setattr(donation, key, value.value if hasattr(value, "value") and key == "donation_type" else value)

        # Keep the auto-created ledger entry in sync - otherwise an edited
        # amount/payment mode silently goes stale in the finance tab.
        income = self._linked_income(donation_id)
        if income:
            if "amount" in fields and fields["amount"] is not None:
                income.amount = donation.amount
            if "payment_mode" in fields and fields["payment_mode"] is not None:
                income.payment_mode = donation.payment_mode
            if "donated_on" in fields and fields["donated_on"] is not None:
                income.received_at = donation.donated_on

        self.db.commit()
        return self.get(donation_id)

    def issue_receipt(self, donation_id: int) -> Donation:
        """Assign a sequential receipt number (idempotent)."""
        donation = self.get(donation_id)
        if donation.receipt_number:
            return donation

        prefix = f"DON-{datetime.now().year}-"
        for _ in range(5):  # retry if two staff issue receipts at the same instant
            last = self.repo.last_receipt_number(prefix)
            try:
                sequence = int(last.rsplit("-", 1)[-1]) + 1 if last else 1
            except ValueError:
                sequence = 1
            donation.receipt_number = f"{prefix}{sequence:06d}"
            donation.receipt_generated_at = datetime.now()
            try:
                self.db.commit()
                return donation
            except IntegrityError:
                self.db.rollback()
                donation = self.get(donation_id)
        raise HTTPException(status_code=503, detail="Could not allocate a receipt number, please retry")

    def archive_receipt(self, donation: Donation, pdf_bytes: bytes) -> None:
        """Best-effort S3 archive of a generated receipt PDF. Never raises - a
        storage hiccup must not block staff from getting the receipt."""
        from app.services.storage_service import StorageService

        storage = StorageService()
        if not storage.enabled:
            return
        try:
            key = storage.upload_private(
                pdf_bytes, f"receipts/{donation.receipt_number}.pdf", "application/pdf"
            )
            donation.receipt_s3_key = key
            self.db.commit()
        except Exception:
            logging.getLogger(__name__).warning(
                "Failed to archive receipt PDF to S3 for donation #%s", donation.id, exc_info=True
            )
