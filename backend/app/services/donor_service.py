from app.repositories.donor_repo import DonorRepository
from app.schemas.donor import DonorCreate
from app.models.donor import Donor

from fastapi import HTTPException


class DonorService:
    def __init__(self, repository: DonorRepository):
        self.repository = repository

    def list_donors(self):
        return self.repository.get_all()

    def get_donor(self, donor_id: int):
        return self.repository.get_by_id(donor_id)

    def create_donor(self, data: DonorCreate):
        if data.amount <= 0:
            raise HTTPException(status_code=400, detail="Donation amount must be greater than zero")

        # Drop unset/None values so model defaults (donated_on = now, payment_mode)
        # apply; passing donated_on=None explicitly would insert NULL into a
        # NOT NULL column.
        payload = {k: v for k, v in data.model_dump().items() if v is not None}
        donor = Donor(**payload)
        return self.repository.create(donor)

    def update_donor(self, donor_id: int, data: dict):
        donor = self.get_donor(donor_id)
        if not donor:
            raise HTTPException(status_code=404, detail="Donor not found")
        
        if "amount" in data and data["amount"] is not None and data["amount"] <= 0:
            raise HTTPException(status_code=400, detail="Donation amount must be greater than zero")

        # Non-nullable columns must never be blanked by an explicit null in the payload.
        for non_nullable in ("name", "amount", "donated_on", "payment_mode", "is_active"):
            if non_nullable in data and data[non_nullable] is None:
                del data[non_nullable]

        return self.repository.update(donor, data)

    def delete_donor(self, donor_id: int):
        donor = self.get_donor(donor_id)
        if not donor:
            raise HTTPException(status_code=404, detail="Donor not found")
        return self.repository.delete(donor)
