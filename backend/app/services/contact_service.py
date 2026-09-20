from app.repositories.contact_repo import ContactRepository
from app.models.contact import ContactMessage, ContactStatus
from app.schemas.contact import ContactCreate, ContactUpdate
from typing import List, Optional
from fastapi import HTTPException

class ContactService:
    def __init__(self, repository: ContactRepository):
        self.repository = repository

    def submit_message(self, schema: ContactCreate) -> ContactMessage:
        message = ContactMessage(
            name=schema.name,
            email=schema.email,
            subject=schema.subject,
            message=schema.message,
            status=ContactStatus.PENDING
        )
        return self.repository.create(message)

    def query_messages(self, status: Optional[ContactStatus] = None):
        return self.repository.query(status)

    def list_messages(self, status: Optional[ContactStatus] = None) -> List[ContactMessage]:
        return self.repository.get_all(status)

    def get_message_details(self, message_id: int) -> ContactMessage:
        message = self.repository.get_by_id(message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        return message

    def update_message(self, message_id: int, schema: ContactUpdate) -> ContactMessage:
        message = self.get_message_details(message_id)
        
        if schema.status:
            message.status = schema.status
        if schema.admin_notes is not None:
            message.admin_notes = schema.admin_notes
            
        return self.repository.update(message)

    def delete_message(self, message_id: int) -> None:
        message = self.get_message_details(message_id)
        self.repository.delete(message)
