from app.repositories.member_repo import MemberRepository
from app.repositories.user_repo import UserRepository
from app.schemas.member import MemberCreate, MemberUpdate
from app.models.member import Member
from fastapi import HTTPException


class MemberService:
    def __init__(self, repository: MemberRepository, user_repository: UserRepository):
        self.repository = repository
        self.user_repository = user_repository

    def list_members(self):
        return self.repository.get_all()

    def get_member(self, member_id: int):
        member = self.repository.get_by_id(member_id)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        return member

    def create_member(self, data: MemberCreate):
        # Validate user exists
        user = self.user_repository.get_by_id(data.user_id)
        if not user:
             raise HTTPException(status_code=404, detail="User not found")
        
        # Validate user roles (Only ADMIN, TRUSTEE, STAFF, SUPER_ADMIN can be members)
        allowed_roles = {"SUPER_ADMIN", "ADMIN", "TRUSTEE", "STAFF"}
        user_roles = set(user.roles or [])
        if not (user_roles & allowed_roles):
             raise HTTPException(
                 status_code=400, 
                 detail="User must have one of ADMIN, TRUSTEE, STAFF, or SUPER_ADMIN roles to have a member profile"
             )
        
        # Prevent duplicate member profiles for the same user
        existing = self.repository.get_by_user_id(data.user_id)
        if existing:
            raise HTTPException(status_code=400, detail="Member profile already exists for this user")

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
