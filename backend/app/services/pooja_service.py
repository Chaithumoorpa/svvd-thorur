from fastapi import HTTPException

from app.models.pooja import Pooja
from app.repositories.pooja_repo import PoojaRepository
from app.schemas.pooja import PoojaCreate, PoojaUpdate


class PoojaService:
    def __init__(self, pooja_repository: PoojaRepository):
        self.repo = pooja_repository

    def list_active_poojas(self):
        return self.repo.get_all()

    def query_all(self):
        return self.repo.query_all()

    def get_pooja(self, pooja_id: int, public: bool = True) -> Pooja:
        pooja = self.repo.get_by_id(pooja_id)
        if not pooja or (public and not pooja.is_active):
            raise HTTPException(status_code=404, detail="Pooja not found")
        return pooja

    def create_pooja(self, data: PoojaCreate) -> Pooja:
        if self.repo.get_by_name(data.name):
            raise HTTPException(status_code=400, detail="Pooja with this name already exists")
        return self.repo.create(Pooja(**data.model_dump()))

    def update_pooja(self, pooja_id: int, data: PoojaUpdate) -> Pooja:
        pooja = self.get_pooja(pooja_id, public=False)
        fields = data.model_dump(exclude_unset=True)

        new_name = fields.get("name")
        if new_name and new_name != pooja.name and self.repo.get_by_name(new_name):
            raise HTTPException(status_code=400, detail="Pooja with this name already exists")

        for key, value in fields.items():
            if key in ("name", "pooja_type", "is_paid", "is_active", "sort_order") and value is None:
                continue
            setattr(pooja, key, value)

        if pooja.start_time and pooja.end_time and pooja.end_time <= pooja.start_time:
            raise HTTPException(status_code=422, detail="End time must be after start time")
        if pooja.is_paid and pooja.suggested_amount is None:
            raise HTTPException(status_code=422, detail="A paid seva needs an amount")
        return self.repo.update(pooja)

    def delete_pooja(self, pooja_id: int) -> Pooja:
        return self.repo.delete(self.get_pooja(pooja_id, public=False))
