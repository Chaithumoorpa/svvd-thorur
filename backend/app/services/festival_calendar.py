"""The temple's recurring festival calendar - every date computed from the
panchang (app/services/panchang.py) for the temple's location, so the
Festivals page and the automatic announcements never run dry.

FestivalCalendarService.fill() is run daily by the festival-announcement cron
job: it adds each upcoming occurrence (next FILL_DAYS days) as an ordinary
Festival row, keyed by `source_key` so re-running never duplicates one and a
row the admin edits or hides stays as they left it.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional

from app.core.config import settings
from app.models.festival import Festival
from app.repositories.festival_repo import FestivalRepository
from app.services import panchang
from app.services.panchang import LunarMonth, Place

FILL_DAYS = 365


@dataclass(frozen=True)
class Occurrence:
    key: str                 # stable id: rule key + date
    name: str
    description: str
    start: date
    end: Optional[date] = None
    festival_type: str = "annual"
    auto_announce: bool = True
    announce_days_before: int = 2


@dataclass(frozen=True)
class TithiRule:
    """`tithi` of lunar `month` (every month if None), observed on the day it
    prevails at `kala`. `until` optionally makes it a span ending on another
    tithi of the same month (Ganesh Navaratri ends on Ananta Chaturdashi)."""
    key: str
    name: str
    description: str
    tithi: int
    kala: str
    month: Optional[str] = None
    until: Optional[tuple[int, str]] = None
    festival_type: str = "annual"
    auto_announce: bool = True
    announce_days_before: int = 3


SHUKLA, KRISHNA = 0, 15  # add to a paksha's tithi number (1-15) for tithi_at's 1-30

MONTHLY: List[TithiRule] = [
    TithiRule("sankashti-chaturthi", "Sankashti Chaturthi",
              "Monthly Sankashti Chaturthi vratam for Lord Vinayaka - special abhishekam and "
              "archana; the fast is broken after moonrise.",
              KRISHNA + 4, "moonrise", festival_type="monthly", announce_days_before=2),
    TithiRule("vinayaka-chaturthi", "Masa Vinayaka Chaturthi",
              "Monthly Vinayaka Chaturthi - special pooja to Sri Varasidhi Vinayaka Swamy.",
              SHUKLA + 4, "madhyahna", festival_type="monthly", auto_announce=False),
]

ANNUAL: List[TithiRule] = [
    TithiRule("ugadi", "Ugadi", "Telugu New Year - panchanga sravanam at the temple.",
              SHUKLA + 1, "sunrise", month="Chaitra", announce_days_before=5),
    TithiRule("sri-rama-navami", "Sri Rama Navami", "Sri Sitarama Kalyanam.",
              SHUKLA + 9, "madhyahna", month="Chaitra", announce_days_before=5),
    TithiRule("akshaya-tritiya", "Akshaya Tritiya", "Akshaya Tritiya special pooja.",
              SHUKLA + 3, "purvahna", month="Vaishakha"),
    TithiRule("guru-purnima", "Guru Purnima", "Guru Purnima (Vyasa Purnima).",
              SHUKLA + 15, "sunrise", month="Ashadha"),
    TithiRule("krishna-janmashtami", "Sri Krishna Janmashtami", "Sri Krishna Janmashtami.",
              KRISHNA + 8, "sunrise", month="Shravana"),
    TithiRule("ganesh-chaturthi", "Vinayaka Chaturthi (Ganesh Navaratri)",
              "The temple's main festival - Vinayaka Chavithi and the Navaratri celebrations "
              "through to nimajjanam on Ananta Chaturdashi.",
              SHUKLA + 4, "madhyahna", month="Bhadrapada", until=(SHUKLA + 14, "sunrise"),
              announce_days_before=7),
    TithiRule("devi-navaratri", "Dasara Devi Navaratri", "Devi Navaratri celebrations through Vijayadashami.",
              SHUKLA + 1, "sunrise", month="Ashvina", until=(SHUKLA + 10, "aparahna"),
              announce_days_before=5),
    TithiRule("vijayadashami", "Vijayadashami (Dasara)", "Vijayadashami - Shami pooja.",
              SHUKLA + 10, "aparahna", month="Ashvina"),
    TithiRule("deepavali", "Deepavali", "Deepavali - Lakshmi pooja in the evening.",
              KRISHNA + 15, "pradosh", month="Ashvina", announce_days_before=5),
    TithiRule("nagula-chavithi", "Nagula Chavithi", "Nagula Chavithi.",
              SHUKLA + 4, "madhyahna", month="Kartika"),
    TithiRule("karthika-purnima", "Karthika Purnima", "Karthika Purnima - Karthika deepam.",
              SHUKLA + 15, "sunrise", month="Kartika"),
    TithiRule("vasant-panchami", "Vasant Panchami", "Sri Panchami - Saraswati pooja.",
              SHUKLA + 5, "purvahna", month="Magha"),
    TithiRule("ratha-saptami", "Ratha Saptami", "Ratha Saptami - Surya pooja.",
              SHUKLA + 7, "sunrise", month="Magha"),
    TithiRule("maha-shivaratri", "Maha Shivaratri", "Maha Shivaratri - abhishekam through the night.",
              KRISHNA + 14, "nishita", month="Magha", announce_days_before=5),
]


def temple_place() -> Place:
    return Place(settings.TEMPLE_LATITUDE, settings.TEMPLE_LONGITUDE, settings.TEMPLE_ELEVATION)


def _occurrence(rule: TithiRule, place: Place, month: LunarMonth) -> Occurrence:
    start = panchang.observance_day(place, month, rule.tithi, rule.kala)
    end = panchang.observance_day(place, month, *rule.until) if rule.until else None
    name = f"{rule.name} ({'Adhika ' if month.adhika else ''}{month.name})" if rule.month is None else rule.name
    return Occurrence(
        key=f"{rule.key}:{start.isoformat()}", name=name, description=rule.description, start=start,
        end=end if end and end > start else None, festival_type=rule.festival_type,
        auto_announce=rule.auto_announce, announce_days_before=rule.announce_days_before,
    )


def _makara_sankranti(place: Place, year: int) -> Occurrence:
    """The sun enters sidereal Makara; after sunset, it's kept the next day."""
    moment = panchang.sankranti(9, date(year, 1, 14))
    day = moment.date()
    if moment >= panchang.sunset(place, day):
        day += timedelta(days=1)
    return Occurrence(key=f"makara-sankranti:{day.isoformat()}", name="Makara Sankranti",
                      description="Sankranti - Bhogi, Sankranti and Kanuma.", start=day,
                      announce_days_before=5)


def _vaikuntha_ekadashi(place: Place, months: List[LunarMonth]) -> List[Occurrence]:
    """The Shukla Ekadashi while the sun is in Dhanu (mid-December to mid-January)."""
    found = []
    for month in months:
        if month.adhika:
            continue
        day = panchang.observance_day(place, month, SHUKLA + 11, "sunrise")
        if panchang.rasi_of_sun(panchang.sunrise(place, day)) == 8:  # Dhanu
            found.append(Occurrence(key=f"vaikuntha-ekadashi:{day.isoformat()}", name="Vaikuntha Ekadashi",
                                    description="Vaikuntha Ekadashi - Uttara dwara darshanam.", start=day,
                                    announce_days_before=5))
    return found


def _varalakshmi_vratam(place: Place, months: List[LunarMonth]) -> List[Occurrence]:
    """The Friday on or before Shravana Purnima."""
    found = []
    for month in months:
        if month.name == "Shravana" and not month.adhika:
            purnima = panchang.observance_day(place, month, SHUKLA + 15, "sunrise")
            day = purnima - timedelta(days=(purnima.weekday() - 4) % 7)
            found.append(Occurrence(key=f"varalakshmi-vratam:{day.isoformat()}", name="Varalakshmi Vratam",
                                    description="Varalakshmi Vratam - collective vratam at the temple.",
                                    start=day))
    return found


def occurrences(start: date, end: date, place: Optional[Place] = None) -> List[Occurrence]:
    """Every festival starting between start and end (inclusive), by date."""
    place = place or temple_place()
    months = panchang.lunar_months(start, end)
    found: List[Occurrence] = []
    for month in months:
        for rule in MONTHLY:
            found.append(_occurrence(rule, place, month))
        if not month.adhika:
            for rule in ANNUAL:
                if rule.month == month.name:
                    found.append(_occurrence(rule, place, month))
    for year in range(start.year, end.year + 1):
        found.append(_makara_sankranti(place, year))
    found += _vaikuntha_ekadashi(place, months) + _varalakshmi_vratam(place, months)
    return sorted((o for o in found if start <= o.start <= end), key=lambda o: (o.start, o.name))


class FestivalCalendarService:
    def __init__(self, repo: FestivalRepository):
        self.repo = repo

    def fill(self, today: Optional[date] = None, days: int = FILL_DAYS) -> List[Festival]:
        """Adds every computed festival in the next `days` days that isn't
        there yet. Existing rows - including ones an admin edited or hid - are
        never touched."""
        today = today or date.today()
        wanted = occurrences(today, today + timedelta(days=days))
        existing = self.repo.existing_source_keys([o.key for o in wanted])
        created = []
        for o in wanted:
            if o.key in existing:
                continue
            created.append(self.repo.create(Festival(
                name=o.name, description=o.description, festival_date=o.start, end_date=o.end,
                festival_type=o.festival_type, auto_announce=o.auto_announce,
                announce_days_before=o.announce_days_before, source_key=o.key,
            )))
        return created
