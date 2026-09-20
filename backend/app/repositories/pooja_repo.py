from app.models.pooja import Pooja
from app.repositories.base import BaseRepository


class PoojaRepository(BaseRepository):
    # Admin-defined order first, then by time of day (untimed last), name, id.
    _ORDER = (
        Pooja.sort_order.asc(),
        Pooja.start_time.is_(None).asc(),
        Pooja.start_time.asc(),
        Pooja.name.asc(),
        Pooja.id.asc(),
    )

    def query_active(self):
        return self.db.query(Pooja).filter(Pooja.is_active.is_(True)).order_by(*self._ORDER)

    def query_all(self):
        return self.db.query(Pooja).order_by(*self._ORDER)

    def get_all(self):
        return self.query_active().all()

    def get_by_id(self, pooja_id: int):
        return self.db.query(Pooja).filter(Pooja.id == pooja_id).first()

    def get_by_name(self, name: str):
        return self.db.query(Pooja).filter(Pooja.name == name).first()

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
        """Soft delete: seva tickets reference poojas, so rows must never disappear."""
        pooja.is_active = False
        return self.update(pooja)

    def count(self) -> int:
        return self.db.query(Pooja).filter(Pooja.is_active.is_(True)).count()
