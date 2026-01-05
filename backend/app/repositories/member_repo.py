from sqlalchemy.orm import Session
from app.models.member import Member
from app.repositories.base import BaseRepository


class MemberRepository(BaseRepository):

    def get_all(self):
        """
        Get all active members ordered by position (role), then name.
        This groups members by role and ensures stable ordering for UI alignment.
        
        Expected order:
        1. Trustees (alphabetically by name)
        2. Staff (alphabetically by name)
        3. Volunteers (alphabetically by name)
        """
        return (
            self.db.query(Member)
            .filter(Member.is_active == True)
            .order_by(
                Member.position.asc(),  # Group by role (Trustee < Staff < Volunteer)
                Member.name.asc()       # Then alphabetically within each role
            )
            .all()
        )

    def get_by_id(self, member_id: int):
        return (
            self.db.query(Member)
            .filter(Member.id == member_id)
            .first()
        )

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
        # soft delete
        member.is_active = False
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def count(self) -> int:
        return self.db.query(Member).filter(Member.is_active == True).count()
