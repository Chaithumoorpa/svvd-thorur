from sqlalchemy.orm import Session
from app.models.donor import Donor
from app.repositories.base import BaseRepository


class DonorRepository(BaseRepository):

    def get_all(self):
        return (
            self.db.query(Donor)
            .filter(Donor.is_active == True)
            .all()
        )

    def get_by_id(self, donor_id: int):
        return (
            self.db.query(Donor)
            .filter(Donor.id == donor_id)
            .first()
        )

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
        donor.is_active = False
        self.db.commit()
        return donor

    def count(self) -> int:
        return self.db.query(Donor).filter(Donor.is_active == True).count()
