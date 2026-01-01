from sqlalchemy.orm import Session
from app.models.pooja import Pooja
from app.repositories.base import BaseRepository

class PoojaRepository(BaseRepository):

    def get_all(self):
        return (
            self.db.query(Pooja)
            .filter(Pooja.is_active == True)
            .all()
        )

    def get_by_id(self, pooja_id: int):
        return (
            self.db.query(Pooja)
            .filter(Pooja.id == pooja_id)
            .first()
        )

    def get_by_name(self, name: str):
        return (
            self.db.query(Pooja)
            .filter(Pooja.name == name)
            .first()
        )

    def create(self, pooja: Pooja):
        self.db.add(pooja)
        self.db.commit()
        self.db.refresh(pooja)
        return pooja

    def update(self, pooja: Pooja):
        self.db.add(pooja)
        self.db.commit()
        self.db.refresh(pooja)
        return pooja

    def delete(self, pooja: Pooja):
        self.db.delete(pooja)
        self.db.commit()
        return pooja

    def count(self) -> int:
        return self.db.query(Pooja).filter(Pooja.is_active == True).count()