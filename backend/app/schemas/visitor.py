from pydantic import BaseModel
from datetime import date

class VisitorStats(BaseModel):
    total_visitors: int
    today_visitors: int

class VisitorTrack(BaseModel):
    ip_hash: str
    visit_date: date
