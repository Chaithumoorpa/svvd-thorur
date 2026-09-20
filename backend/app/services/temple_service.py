from typing import List

from fastapi import HTTPException

from app.models.temple import Temple
from app.models.temple_timing import TempleTiming
from app.repositories.temple_repo import TempleRepository
from app.schemas.temple import TempleUpdate, TimingCreate, TimingUpdate


class TempleService:
    def __init__(self, repository: TempleRepository):
        self.repository = repository

    # ---- profile -------------------------------------------------------------------
    def get_profile(self) -> Temple:
        temple = self.repository.get_active()
        if not temple:
            raise HTTPException(status_code=404, detail="Temple profile has not been set up yet")
        return temple

    def update_profile(self, data: TempleUpdate) -> Temple:
        fields = data.model_dump(exclude_unset=True)
        temple = self.repository.get_active()
        if not temple:
            if not fields.get("name"):
                raise HTTPException(status_code=400, detail="Temple name is required")
            temple = Temple(name=fields["name"])
        for key, value in fields.items():
            if key == "name" and not value:
                continue  # name is mandatory; ignore attempts to blank it
            setattr(temple, key, value)
        return self.repository.save(temple)

    # ---- timings -------------------------------------------------------------------
    def list_timings(self, active_only: bool = True) -> List[TempleTiming]:
        return self.repository.list_timings(active_only)

    def _get_timing(self, timing_id: int) -> TempleTiming:
        timing = self.repository.get_timing(timing_id)
        if not timing:
            raise HTTPException(status_code=404, detail="Timing not found")
        return timing

    def create_timing(self, data: TimingCreate) -> TempleTiming:
        return self.repository.save_timing(TempleTiming(**data.model_dump()))

    def update_timing(self, timing_id: int, data: TimingUpdate) -> TempleTiming:
        timing = self._get_timing(timing_id)
        fields = data.model_dump(exclude_unset=True)
        start = fields.get("start_time", timing.start_time)
        end = fields.get("end_time", timing.end_time)
        if end <= start:  # validate the merged result BEFORE touching the row
            raise HTTPException(status_code=422, detail="End time must be after start time")
        for key, value in fields.items():
            setattr(timing, key, value)
        return self.repository.save_timing(timing)

    def delete_timing(self, timing_id: int) -> TempleTiming:
        timing = self._get_timing(timing_id)
        self.repository.delete_timing(timing)
        return timing
