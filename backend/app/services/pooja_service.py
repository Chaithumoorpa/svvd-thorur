from app.repositories.pooja_repo import PoojaRepository
from app.repositories.pooja_repo import PoojaRepository
from app.schemas.pooja import PoojaCreate, PoojaUpdate
from app.models.pooja import Pooja

from fastapi import HTTPException

class PoojaService:
    def __init__(self, pooja_repository: PoojaRepository):
        self.pooja_repository = pooja_repository

    def list_active_poojas(self):
        """
        Returns all active poojas.
        Business rules can be added here later.
        """
        return self.pooja_repository.get_all()

    def get_pooja_details(self, pooja_id: int):
        """
        Returns a single pooja by id.
        """
        return self.pooja_repository.get_by_id(pooja_id)

    def create_pooja(self, data: PoojaCreate):
        existing = self.pooja_repository.get_by_name(data.name)
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Pooja with this name already exists"
            )

        pooja = Pooja(**data.dict())
        return self.pooja_repository.create(pooja)

    def update_pooja(self, pooja_id: int, data: PoojaUpdate):
        pooja = self.pooja_repository.get_by_id(pooja_id)
        if not pooja:
            raise HTTPException(status_code=404, detail="Pooja not found")

        # Check name uniqueness if name is being updated and it's different
        if data.name and data.name != pooja.name:
            existing = self.pooja_repository.get_by_name(data.name)
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="Pooja with this name already exists"
                )

        for key, value in data.dict(exclude_unset=True).items():
            setattr(pooja, key, value)
            
        return self.pooja_repository.update(pooja)

    def delete_pooja(self, pooja_id: int):
        pooja = self.pooja_repository.get_by_id(pooja_id)
        if not pooja:
            raise HTTPException(status_code=404, detail="Pooja not found")
            
        return self.pooja_repository.delete(pooja)
