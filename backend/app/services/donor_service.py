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

        payload = data.dict()
        # if donated_on is None, model default will apply
        donor = Donor(**payload)
        return self.repository.create(donor)

    def update_donor(self, donor_id: int, data: dict):
        donor = self.get_donor(donor_id)
        if not donor:
            raise HTTPException(status_code=404, detail="Donor not found")
        
        if "amount" in data and data["amount"] is not None and data["amount"] <= 0:
            raise HTTPException(status_code=400, detail="Donation amount must be greater than zero")

        return self.repository.update(donor, data)

    def delete_donor(self, donor_id: int):
        donor = self.get_donor(donor_id)
        if not donor:
            raise HTTPException(status_code=404, detail="Donor not found")
        return self.repository.delete(donor)
