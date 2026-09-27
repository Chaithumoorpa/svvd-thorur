from datetime import date as date_, datetime, timedelta
from typing import List
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.abhishekam import (
    ABHISHEKAM_FEE, ABHISHEKAM_VISIBILITY_DAYS, Abhishekam, AbhishekamPaymentStatus, AbhishekamVisibility,
    DAILY_SLOT_CAP,
)
from app.models.finance import IncomeSourceType, IncomeTransaction, PaymentMode
from app.schemas.abhishekam import (
    AbhishekamCalendarDay, AbhishekamCreate, AbhishekamDayEntry, AbhishekamDayFlyer, AbhishekamPersonalPageOut,
)

# A booking counts toward the day's cap as soon as it's submitted (PENDING) -
# not just once paid - otherwise more than DAILY_SLOT_CAP people could all be
# told "you're in" for the same date before any of them actually pays.
_HOLDS_A_SLOT = (AbhishekamPaymentStatus.PENDING, AbhishekamPaymentStatus.PAID)


class AbhishekamService:
    def __init__(self, db: Session):
        self.db = db

    def _generate_reference_number(self) -> str:
        prefix = f"ABHI-{datetime.now().year}-"
        last = (
            self.db.query(Abhishekam.reference_number)
            .filter(Abhishekam.reference_number.like(f"{prefix}%"))
            .order_by(Abhishekam.reference_number.desc())
            .first()
        )
        try:
            sequence = int(last[0].rsplit("-", 1)[-1]) + 1 if last else 1
        except (ValueError, IndexError):
            sequence = 1
        return f"{prefix}{sequence:06d}"

    def slots_used(self, occasion_date: date_) -> int:
        return (
            self.db.query(Abhishekam)
            .filter(Abhishekam.occasion_date == occasion_date, Abhishekam.payment_status.in_(_HOLDS_A_SLOT))
            .count()
        )

    def create(self, data: AbhishekamCreate) -> Abhishekam:
        """Fee is always ABHISHEKAM_FEE - never taken from the client. Capped
        at DAILY_SLOT_CAP per date, same idea as the temple's paper register.
        Retries on a reference-number collision, same pattern as seva ticket
        numbers."""
        if self.slots_used(data.occasion_date) >= DAILY_SLOT_CAP:
            raise HTTPException(
                status_code=409,
                detail=f"{data.occasion_date.isoformat()} is fully booked for Abhishekam "
                       f"({DAILY_SLOT_CAP}/{DAILY_SLOT_CAP} slots taken). Please choose another date.",
            )
        for _ in range(5):
            abhishekam = Abhishekam(
                reference_number=self._generate_reference_number(),
                devotee_name=data.devotee_name,
                mobile_number=data.mobile_number,
                email=data.email,
                occasion=data.occasion,
                occasion_date=data.occasion_date,
                relation=data.relation,
                message=data.message,
                photo_url=data.photo_url,
                visibility=data.visibility,
                amount=ABHISHEKAM_FEE,
                payment_status=AbhishekamPaymentStatus.PENDING,
            )
            self.db.add(abhishekam)
            try:
                self.db.commit()
                return abhishekam
            except IntegrityError:
                self.db.rollback()
        raise HTTPException(status_code=503, detail="Could not allocate a reference number, please retry")

    def get(self, abhishekam_id: UUID) -> Abhishekam:
        row = self.db.query(Abhishekam).filter(Abhishekam.id == abhishekam_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Abhishekam booking not found")
        return row

    def collect_payment(self, abhishekam_id: UUID, admin_user) -> Abhishekam:
        """Marks a PENDING booking as PAID once the devotee pays Rs {ABHISHEKAM_FEE}
        at the temple counter, and records the cash income - the private page
        becomes visible for ABHISHEKAM_VISIBILITY_DAYS starting now."""
        row = self.get(abhishekam_id)
        if row.payment_status != AbhishekamPaymentStatus.PENDING:
            raise HTTPException(status_code=400, detail="This booking has no pending payment to collect")

        row.payment_status = AbhishekamPaymentStatus.PAID
        row.paid_at = datetime.now()
        row.collected_by_admin_id = admin_user.id
        self.db.add(IncomeTransaction(
            source_type=IncomeSourceType.ABHISHEKAM,
            reference_id=f"abhishekam:{row.id}",
            amount=row.amount,
            payment_mode=PaymentMode.CASH,
            received_by=admin_user.id,
            notes=f"Abhishekam {row.reference_number} - {row.devotee_name} ({row.occasion})",
        ))
        self.db.commit()
        self.db.refresh(row)
        return row

    def query_pending(self):
        return (
            self.db.query(Abhishekam)
            .filter(Abhishekam.payment_status == AbhishekamPaymentStatus.PENDING)
            .order_by(Abhishekam.created_at.desc())
        )

    def query_all(self):
        return self.db.query(Abhishekam).order_by(Abhishekam.created_at.desc())

    def personal_page(self, abhishekam_id: UUID) -> AbhishekamPersonalPageOut:
        row = self.get(abhishekam_id)
        base = {
            "reference_number": row.reference_number,
            "occasion": row.occasion,
            "occasion_date": row.occasion_date,
        }
        if row.payment_status == AbhishekamPaymentStatus.PENDING:
            return AbhishekamPersonalPageOut(status="pending", **base)

        expires_at = row.paid_at + timedelta(days=ABHISHEKAM_VISIBILITY_DAYS)
        if datetime.now() > expires_at:
            return AbhishekamPersonalPageOut(status="expired", **base)

        return AbhishekamPersonalPageOut(
            status="active",
            devotee_name=row.devotee_name,
            relation=row.relation,
            message=row.message,
            photo_url=row.photo_url,
            expires_at=expires_at,
            **base,
        )

    def calendar_year(self, year: int) -> List[AbhishekamCalendarDay]:
        """Every day of `year`, with how many slots are taken - the public
        365-day grid. A single grouped query for the whole year, then filled
        in with zeroes for the days with no bookings at all."""
        rows = (
            self.db.query(Abhishekam.occasion_date, func.count(Abhishekam.id))
            .filter(
                func.extract("year", Abhishekam.occasion_date) == year,
                Abhishekam.payment_status.in_(_HOLDS_A_SLOT),
            )
            .group_by(Abhishekam.occasion_date)
            .all()
        )
        counts = {d: c for d, c in rows}

        days: List[AbhishekamCalendarDay] = []
        current = date_(year, 1, 1)
        while current.year == year:
            days.append(AbhishekamCalendarDay(
                date=current, slots_used=counts.get(current, 0), slots_total=DAILY_SLOT_CAP,
            ))
            current += timedelta(days=1)
        return days

    def day_flyer(self, occasion_date: date_) -> AbhishekamDayFlyer:
        """PUBLIC + PAID bookings only - a PRIVATE or still-PENDING booking
        never appears here, even though it still holds a slot (see slots_used
        above, which counts both)."""
        public_paid = (
            self.db.query(Abhishekam)
            .filter(
                Abhishekam.occasion_date == occasion_date,
                Abhishekam.payment_status == AbhishekamPaymentStatus.PAID,
                Abhishekam.visibility == AbhishekamVisibility.PUBLIC,
            )
            .order_by(Abhishekam.created_at.asc())
            .all()
        )
        return AbhishekamDayFlyer(
            date=occasion_date,
            slots_used=self.slots_used(occasion_date),
            slots_total=DAILY_SLOT_CAP,
            entries=[
                AbhishekamDayEntry(devotee_name=r.devotee_name, occasion=r.occasion, photo_url=r.photo_url)
                for r in public_paid
            ],
        )
