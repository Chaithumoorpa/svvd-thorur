from fastapi import HTTPException

from app.models.member import Member
from app.repositories.member_repo import MemberRepository
from app.schemas.member import MemberCreate, MemberUpdate


class MemberService:
    def __init__(self, repository: MemberRepository):
        self.repository = repository

    def query_members(self):
        return self.repository.query_active()

    def list_members(self):
        return self.repository.get_all()

    def list_public(self):
        return self.repository.get_public()

    def get_member(self, member_id: int) -> Member:
        member = self.repository.get_by_id(member_id)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        return member

    def create_member(self, data: MemberCreate) -> Member:
        return self.repository.create(Member(**data.model_dump()))

    def update_member(self, member_id: int, data: MemberUpdate) -> Member:
        member = self.get_member(member_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            if field in ("name", "phone") and value is None:
                continue  # required columns can't be cleared
            setattr(member, field, value)
        return self.repository.update(member)

    def delete_member(self, member_id: int) -> Member:
        return self.repository.delete(self.get_member(member_id))
