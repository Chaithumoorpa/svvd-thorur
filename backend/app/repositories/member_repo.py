from typing import List

from app.models.member import Member
from app.repositories.base import BaseRepository


class MemberRepository(BaseRepository):
    # Explicit display order chosen by the temple (sort_order), then name, then id.
    _ORDER = (Member.sort_order.asc(), Member.name.asc(), Member.id.asc())

    def query_active(self):
        return self.db.query(Member).filter(Member.is_active.is_(True)).order_by(*self._ORDER)

    def get_all(self) -> List[Member]:
        return self.query_active().all()

    def get_public(self) -> List[Member]:
        """Members the temple chose to publish (name/position/photo only - see schema)."""
        return (
            self.db.query(Member)
            .filter(Member.is_active.is_(True), Member.show_on_website.is_(True))
            .order_by(*self._ORDER)
            .all()
        )

    def get_by_id(self, member_id: int):
        return self.db.query(Member).filter(Member.id == member_id).first()

    def create(self, member: Member):
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def update(self, member: Member):
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def delete(self, member: Member):
        """Soft delete; a deactivated member also disappears from the public site."""
        member.is_active = False
        member.show_on_website = False
        return self.update(member)

    def count(self) -> int:
        return self.db.query(Member).filter(Member.is_active.is_(True)).count()
