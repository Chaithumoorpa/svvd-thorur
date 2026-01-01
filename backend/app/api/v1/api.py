from fastapi import APIRouter
from app.api.v1 import pooja, festival, auth, announcement, meta, members, donors, gallery, seva_tickets, contact, stats, finance

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(meta.router)
api_router.include_router(auth.router)
api_router.include_router(pooja.router)
api_router.include_router(festival.router)
api_router.include_router(announcement.router)
api_router.include_router(members.router)
api_router.include_router(donors.router)
api_router.include_router(gallery.router)
api_router.include_router(seva_tickets.router)
api_router.include_router(contact.router)
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(finance.router, prefix="/finance", tags=["finance"])

