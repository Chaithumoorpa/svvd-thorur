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
    BlessingStatus,
)

# A booking counts toward the day's cap as soon as it's submitted (PENDING) -
# not just once paid - otherwise more than DAILY_SLOT_CAP people could all be
# told "you're in" for the same date before any of them actually pays.
_HOLDS_A_SLOT = (AbhishekamPaymentStatus.PENDING, AbhishekamPaymentStatus.PAID)

MAX_CALENDAR_DAYS = 400  # one request covers the public grid's 365-day window, not arbitrary history


def visible_until(occasion_date: date_) -> date_:
    """Last day (inclusive) a day's blessing pages and photos stay up."""
    return occasion_date + timedelta(days=ABHISHEKAM_VISIBILITY_DAYS - 1)


def blessing_status(occasion_date: date_, today: date_) -> BlessingStatus:
    if today < occasion_date:
        return "upcoming"
    return "active" if today <= visible_until(occasion_date) else "archived"


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
        at the temple counter, and records the cash income. The private page
        opens on occasion_date - see personal_page."""
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

    def personal_page(self, abhishekam_id: UUID, today: date_ | None = None) -> AbhishekamPersonalPageOut:
        """Opens on occasion_date - the same day the greeting email goes out -
        for ABHISHEKAM_VISIBILITY_DAYS, however far ahead the fee was paid."""
        today = today or date_.today()
        row = self.get(abhishekam_id)
        base = {
            "reference_number": row.reference_number,
            "occasion": row.occasion,
            "occasion_date": row.occasion_date,
        }
        if row.payment_status == AbhishekamPaymentStatus.PENDING:
            return AbhishekamPersonalPageOut(status="pending", **base)

        status = blessing_status(row.occasion_date, today)
        if status == "upcoming":
            return AbhishekamPersonalPageOut(status="scheduled", **base)
        if status == "archived":
            return AbhishekamPersonalPageOut(status="expired", **base)
        return AbhishekamPersonalPageOut(
            status="active",
            devotee_name=row.devotee_name,
            relation=row.relation,
            message=row.message,
            photo_url=row.photo_url,
            visible_until=visible_until(row.occasion_date),
            **base,
        )

    def calendar_range(self, start: date_, end: date_) -> List[AbhishekamCalendarDay]:
        """Every day from `start` to `end` inclusive, with how many slots are
        taken - the public contribution-style grid. One grouped query for the
        whole range, filled in with zeroes for days nobody booked."""
        rows = (
            self.db.query(Abhishekam.occasion_date, func.count(Abhishekam.id))
            .filter(
                Abhishekam.occasion_date.between(start, end),
                Abhishekam.payment_status.in_(_HOLDS_A_SLOT),
            )
            .group_by(Abhishekam.occasion_date)
            .all()
        )
        counts = dict(rows)
        return [
            AbhishekamCalendarDay(date=day, slots_used=counts.get(day, 0), slots_total=DAILY_SLOT_CAP)
            for day in (start + timedelta(days=i) for i in range((end - start).days + 1))
        ]

    def day_flyer(self, occasion_date: date_, today: date_ | None = None) -> AbhishekamDayFlyer:
        """PUBLIC + PAID bookings only - a PRIVATE or still-PENDING booking
        never appears here, even though it still holds a slot (see slots_used
        above, which counts both). Photos only while the day is active."""
        today = today or date_.today()
        status = blessing_status(occasion_date, today)
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
        active = status == "active"
        return AbhishekamDayFlyer(
            date=occasion_date,
            slots_used=self.slots_used(occasion_date),
            slots_total=DAILY_SLOT_CAP,
            blessing_status=status,
            visible_until=visible_until(occasion_date),
            entries=[
                AbhishekamDayEntry(
                    devotee_name=r.devotee_name,
                    occasion=r.occasion,
                    relation=r.relation if active else None,
                    photo_url=r.photo_url if active else None,
                )
                for r in public_paid
            ],
        )
