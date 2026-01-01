from sqlalchemy.orm import Session
from app.models.contact import ContactMessage, ContactStatus
from app.repositories.base import BaseRepository
from typing import List, Optional

class ContactRepository(BaseRepository):
    def create(self, message: ContactMessage) -> ContactMessage:
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_all(self, status: Optional[ContactStatus] = None) -> List[ContactMessage]:
        query = self.db.query(ContactMessage)
        if status:
            query = query.filter(ContactMessage.status == status)
        return query.order_by(ContactMessage.created_at.desc()).all()

    def get_by_id(self, message_id: int) -> Optional[ContactMessage]:
        return self.db.query(ContactMessage).filter(ContactMessage.id == message_id).first()

    def update(self, message: ContactMessage) -> ContactMessage:
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def delete(self, message: ContactMessage) -> None:
        self.db.delete(message)
        self.db.commit()
