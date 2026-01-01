from sqlalchemy.orm import Session
from app.models.member import Member
from app.repositories.base import BaseRepository


class MemberRepository(BaseRepository):

    def get_all(self):
        return (
            self.db.query(Member)
            .filter(Member.is_active == True)
            .all()
        )

    def get_by_id(self, member_id: int):
        return (
            self.db.query(Member)
            .filter(Member.id == member_id)
            .first()
        )

    def get_by_user_id(self, user_id: int):
        return (
            self.db.query(Member)
            .filter(Member.user_id == user_id)
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
