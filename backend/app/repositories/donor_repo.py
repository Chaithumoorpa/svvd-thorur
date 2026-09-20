from datetime import datetime
from typing import Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

from app.models.donation import Donation
from app.models.donor import Donor
from app.repositories.base import BaseRepository


def _like(term: str) -> str:
    """Escape LIKE wildcards in user input."""
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


class DonorRepository(BaseRepository):

    def query_with_totals(self, search: Optional[str] = None, include_inactive: bool = False):
        """
        Donors with donation_count / total_donated computed in ONE grouped query
        (no per-donor lookups). Rows are (Donor, count, total).
        """
        totals = (
            self.db.query(
                Donation.donor_id.label("donor_id"),
                func.count(Donation.id).label("cnt"),
                func.coalesce(func.sum(Donation.amount), 0).label("total"),
            )
            .group_by(Donation.donor_id)
            .subquery()
        )
        query = (
            self.db.query(Donor, func.coalesce(totals.c.cnt, 0), func.coalesce(totals.c.total, 0))
            .outerjoin(totals, totals.c.donor_id == Donor.id)
        )
        if not include_inactive:
            query = query.filter(Donor.is_active.is_(True))
        if search:
            pattern = _like(search.strip())
            query = query.filter(
                or_(Donor.name.ilike(pattern, escape="\\"), Donor.phone.ilike(pattern, escape="\\"))
            )
        return query.order_by(Donor.name.asc(), Donor.id.asc())

    def get_all(self):
        return [row[0] for row in self.query_with_totals().all()]

    def get_by_id(self, donor_id: int):
        return self.db.query(Donor).filter(Donor.id == donor_id).first()

    def get_with_totals(self, donor_id: int):
        return self.query_with_totals(include_inactive=True).filter(Donor.id == donor_id).first()

    def create(self, donor: Donor):
        self.db.add(donor)
        self.db.commit()
        self.db.refresh(donor)
        return donor

    def update(self, donor: Donor, data: dict):
        for key, value in data.items():
            setattr(donor, key, value)
        self.db.commit()
        self.db.refresh(donor)
        return donor

    def delete(self, donor: Donor):
        """Soft delete - donation history must survive."""
        donor.is_active = False
        self.db.commit()
        self.db.refresh(donor)
        return donor

    def count(self) -> int:
        return self.db.query(Donor).filter(Donor.is_active.is_(True)).count()


class DonationRepository(BaseRepository):

    def query(self, donor_id: Optional[int] = None, start: Optional[datetime] = None,
              end: Optional[datetime] = None, donation_type: Optional[str] = None):
        query = self.db.query(Donation).options(joinedload(Donation.donor))
        if donor_id:
            query = query.filter(Donation.donor_id == donor_id)
        if start:
            query = query.filter(Donation.donated_on >= start)
        if end:
            query = query.filter(Donation.donated_on < end)
        if donation_type:
            query = query.filter(Donation.donation_type == donation_type)
        return query.order_by(Donation.donated_on.desc(), Donation.id.desc())

    def get_by_id(self, donation_id: int) -> Optional[Donation]:
        return (
            self.db.query(Donation)
            .options(joinedload(Donation.donor))
            .filter(Donation.id == donation_id)
            .first()
        )

    def last_receipt_number(self, prefix: str) -> Optional[str]:
        return (
            self.db.query(func.max(Donation.receipt_number))
            .filter(Donation.receipt_number.like(f"{prefix}%"))
            .scalar()
        )
