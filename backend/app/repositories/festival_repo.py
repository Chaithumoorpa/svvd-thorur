from sqlalchemy.orm import Session
from app.models.festival import Festival
from app.repositories.base import BaseRepository


class FestivalRepository(BaseRepository):

    def get_all(self):
        return (
            self.db.query(Festival)
            .filter(Festival.is_active == True)
            .all()
        )

    def get_by_id(self, festival_id: int):
        return (
            self.db.query(Festival)
            .filter(Festival.id == festival_id)
            .first()
        )

    def get_by_name(self, name: str):
        return (
            self.db.query(Festival)
            .filter(Festival.name == name)
            .first()
        )

    def create(self, festival: Festival):
        self.db.add(festival)
        self.db.commit()
        self.db.refresh(festival)
        return festival
