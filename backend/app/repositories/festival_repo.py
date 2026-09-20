from datetime import date
from typing import Optional

from sqlalchemy import or_

from app.models.festival import Festival
from app.repositories.base import BaseRepository


class FestivalRepository(BaseRepository):
    # Dated festivals first (soonest first), undated last; name/id keep the order stable.
    _ORDER = (
        Festival.festival_date.is_(None).asc(),
        Festival.festival_date.asc(),
        Festival.name.asc(),
        Festival.id.asc(),
    )

    def query_active(self, upcoming_from: Optional[date] = None):
        query = self.db.query(Festival).filter(Festival.is_active.is_(True))
        if upcoming_from:
            # still relevant if it has not ended yet (end_date, else the single festival day)
            query = query.filter(
                or_(
                    Festival.festival_date.is_(None),
                    Festival.end_date >= upcoming_from,
                    Festival.festival_date >= upcoming_from,
                )
            )
        return query.order_by(*self._ORDER)

    def query_all(self):
        return self.db.query(Festival).order_by(*self._ORDER)

    def get_all(self, upcoming_from: Optional[date] = None, limit: Optional[int] = None):
        query = self.query_active(upcoming_from)
        if limit:
            query = query.limit(limit)
        return query.all()

    def get_by_id(self, festival_id: int):
        return self.db.query(Festival).filter(Festival.id == festival_id).first()

    def get_by_name(self, name: str):
        return self.db.query(Festival).filter(Festival.name == name).first()

    def create(self, festival: Festival):
        self.db.add(festival)
        self.db.commit()
        self.db.refresh(festival)
        return festival

    def update(self, festival: Festival):
        self.db.add(festival)
        self.db.commit()
        self.db.refresh(festival)
        return festival
