from typing import List, Optional

from app.models.temple import Temple
from app.models.temple_timing import TempleTiming
from app.repositories.base import BaseRepository


class TempleRepository(BaseRepository):
    # ---- profile (single active row) -------------------------------------------
    def get_active(self) -> Optional[Temple]:
        return (
            self.db.query(Temple)
            .filter(Temple.is_active.is_(True))
            .order_by(Temple.id.asc())
            .first()
        )

    def save(self, temple: Temple) -> Temple:
        self.db.add(temple)
        self.db.commit()
        self.db.refresh(temple)
        return temple

    # ---- timings -----------------------------------------------------------------
    def list_timings(self, active_only: bool = True) -> List[TempleTiming]:
        query = self.db.query(TempleTiming)
        if active_only:
            query = query.filter(TempleTiming.is_active.is_(True))
        return query.order_by(
            TempleTiming.sort_order.asc(), TempleTiming.start_time.asc(), TempleTiming.id.asc()
        ).all()

    def get_timing(self, timing_id: int) -> Optional[TempleTiming]:
        return self.db.query(TempleTiming).filter(TempleTiming.id == timing_id).first()

    def save_timing(self, timing: TempleTiming) -> TempleTiming:
        self.db.add(timing)
        self.db.commit()
        self.db.refresh(timing)
        return timing

    def delete_timing(self, timing: TempleTiming) -> None:
        self.db.delete(timing)
        self.db.commit()
