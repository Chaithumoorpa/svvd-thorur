"""Public views of seva bookings made for an occasion: a seva's booking
calendar (slots per day), a day's public blessings, and each devotee's own
blessing page."""
from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel

BlessingStatus = Literal["upcoming", "active", "archived"]


class SevaCalendarDay(BaseModel):
    """One day's bookings for the public contribution-style grid. slots_total
    is the seva's daily_slot_cap - None when it has no limit."""
    date: date
    slots_used: int
    slots_total: Optional[int] = None


class BlessingEntry(BaseModel):
    """A booking the devotee chose to show publicly, once paid for (or free).
    Name + occasion always - the permanent public timeline; the photo only
    while that day's blessings are active."""
    devotee_name: str
    occasion: str
    photo_url: Optional[str] = None


class SevaDay(BaseModel):
    """A calendar square's pop-up, and that date's public blessings page."""
    date: date
    slots_used: int
    slots_total: Optional[int] = None
    blessing_status: BlessingStatus
    visible_until: date
    entries: List[BlessingEntry]


class PersonalBlessingOut(BaseModel):
    """The devotee's own blessing page (linked from the greeting email):
    - pending: the seva fee isn't paid yet.
    - scheduled: paid (or free), but the seva date hasn't arrived.
    - active: the seva date through visible_until - name and photo shown.
    - expired: afterwards."""
    status: Literal["pending", "scheduled", "active", "expired"]
    seva_name: str
    occasion: str
    seva_date: date
    devotee_name: Optional[str] = None
    photo_url: Optional[str] = None
    visible_until: Optional[date] = None
