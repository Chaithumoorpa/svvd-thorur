from app.repositories.member_repo import MemberRepository
from app.schemas.member import MemberCreate, MemberUpdate
from app.models.member import Member
from fastapi import HTTPException


class MemberService:
    def __init__(self, repository: MemberRepository):
        self.repository = repository

    def list_members(self):
        return self.repository.get_all()

    def get_member(self, member_id: int):
        member = self.repository.get_by_id(member_id)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        return member

    def create_member(self, data: MemberCreate):
        member = Member(**data.dict())
        return self.repository.create(member)

    def update_member(self, member_id: int, data: MemberUpdate):
        member = self.repository.get_by_id(member_id)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")

        for field, value in data.dict(exclude_unset=True).items():
            setattr(member, field, value)

        return self.repository.update(member)

    def delete_member(self, member_id: int):
        member = self.repository.get_by_id(member_id)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        return self.repository.delete(member)
