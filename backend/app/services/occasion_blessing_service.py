from datetime import datetime, timedelta
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.finance import IncomeSourceType, IncomeTransaction, PaymentMode
from app.models.occasion_blessing import (
    BLESSING_FEE, BLESSING_VISIBILITY_DAYS, BlessingPaymentStatus, OccasionBlessing,
)
from app.schemas.occasion_blessing import OccasionBlessingCreate, OccasionBlessingPublicOut


class OccasionBlessingService:
    def __init__(self, db: Session):
        self.db = db

    def _generate_reference_number(self) -> str:
        prefix = f"BLESS-{datetime.now().year}-"
        last = (
            self.db.query(OccasionBlessing.reference_number)
            .filter(OccasionBlessing.reference_number.like(f"{prefix}%"))
            .order_by(OccasionBlessing.reference_number.desc())
            .first()
        )
        try:
            sequence = int(last[0].rsplit("-", 1)[-1]) + 1 if last else 1
        except (ValueError, IndexError):
            sequence = 1
        return f"{prefix}{sequence:06d}"

    def create(self, data: OccasionBlessingCreate) -> OccasionBlessing:
        """Fee is always BLESSING_FEE - never taken from the client. Retries
        on a reference-number collision, same pattern as seva ticket numbers."""
        for _ in range(5):
            blessing = OccasionBlessing(
                reference_number=self._generate_reference_number(),
                devotee_name=data.devotee_name,
                mobile_number=data.mobile_number,
                email=data.email,
                occasion=data.occasion,
                occasion_date=data.occasion_date,
                relation=data.relation,
                message=data.message,
                photo_url=data.photo_url,
                amount=BLESSING_FEE,
                payment_status=BlessingPaymentStatus.PENDING,
            )
            self.db.add(blessing)
            try:
                self.db.commit()
                return blessing
            except IntegrityError:
                self.db.rollback()
        raise HTTPException(status_code=503, detail="Could not allocate a reference number, please retry")

    def get(self, blessing_id: UUID) -> OccasionBlessing:
        blessing = self.db.query(OccasionBlessing).filter(OccasionBlessing.id == blessing_id).first()
        if not blessing:
            raise HTTPException(status_code=404, detail="Occasion Blessing request not found")
        return blessing

    def collect_payment(self, blessing_id: UUID, admin_user) -> OccasionBlessing:
        """Marks a PENDING request as PAID once the devotee pays Rs {BLESSING_FEE}
        at the temple counter, and records the cash income - the private page
        becomes visible for BLESSING_VISIBILITY_DAYS starting now."""
        blessing = self.get(blessing_id)
        if blessing.payment_status != BlessingPaymentStatus.PENDING:
            raise HTTPException(status_code=400, detail="This request has no pending payment to collect")

        blessing.payment_status = BlessingPaymentStatus.PAID
        blessing.paid_at = datetime.now()
        blessing.collected_by_admin_id = admin_user.id
        self.db.add(IncomeTransaction(
            source_type=IncomeSourceType.OCCASION_BLESSING,
            reference_id=f"occasion_blessing:{blessing.id}",
            amount=blessing.amount,
            payment_mode=PaymentMode.CASH,
            received_by=admin_user.id,
            notes=f"Occasion Blessing {blessing.reference_number} - {blessing.devotee_name} ({blessing.occasion})",
        ))
        self.db.commit()
        self.db.refresh(blessing)
        return blessing

    def query_pending(self):
        return (
            self.db.query(OccasionBlessing)
            .filter(OccasionBlessing.payment_status == BlessingPaymentStatus.PENDING)
            .order_by(OccasionBlessing.created_at.desc())
        )

    def query_all(self):
        return self.db.query(OccasionBlessing).order_by(OccasionBlessing.created_at.desc())

    def public_view(self, blessing_id: UUID) -> OccasionBlessingPublicOut:
        blessing = self.get(blessing_id)
        base = {
            "reference_number": blessing.reference_number,
            "occasion": blessing.occasion,
            "occasion_date": blessing.occasion_date,
        }
        if blessing.payment_status == BlessingPaymentStatus.PENDING:
            return OccasionBlessingPublicOut(status="pending", **base)

        expires_at = blessing.paid_at + timedelta(days=BLESSING_VISIBILITY_DAYS)
        if datetime.now() > expires_at:
            return OccasionBlessingPublicOut(status="expired", **base)

        return OccasionBlessingPublicOut(
            status="active",
            devotee_name=blessing.devotee_name,
            relation=blessing.relation,
            message=blessing.message,
            photo_url=blessing.photo_url,
            expires_at=expires_at,
            **base,
        )
