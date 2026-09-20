from typing import List, Optional

from sqlalchemy import func

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(func.lower(User.email) == email.lower()).first()

    def query_all(self):
        """Deterministic ordering: username, then id."""
        return self.db.query(User).order_by(User.username.asc(), User.id.asc())

    def get_all(self) -> List[User]:
        return self.query_all().all()

    def count_active_super_admins(self) -> int:
        # roles is an ARRAY (Postgres) / JSON (sqlite tests): filter in Python, the table is tiny.
        return sum(1 for u in self.db.query(User).filter(User.is_active.is_(True)).all() if u.is_super_admin)

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
