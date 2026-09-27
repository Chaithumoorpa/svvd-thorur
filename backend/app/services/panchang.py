"""Just enough of a Hindu lunisolar calendar (panchang) to date the temple's
festivals, computed from the sun's and moon's positions for the temple's own
location - no yearly data entry, no external service.

- Tithi: the lunar day, 1-30 - which twelfth-of-a-circle the moon has moved
  ahead of the sun (1-15 Shukla paksha, waxing; 16-30 Krishna, waning; 30 is
  Amavasya, 15 Purnima).
- Lunar month (amanta, as in Telangana/Andhra): new moon to new moon, named
  after the sidereal zodiac sign (rasi) the sun is in when it begins - the
  month starting with the sun in Meena is Chaitra. A month in which the sun
  changes no sign is Adhika (an extra month); annual festivals skip it.
- A festival is a tithi in a month, observed on the civil day on which that
  tithi prevails at a given time of that day (its "kala") - moonrise for
  Sankashti Chaturthi, midday for Vinayaka Chaturthi, midnight for Maha
  Shivaratri, and so on - the same rules published panchangs use.

Positions come from PyEphem (VSOP87/ELP2000 theories, well under an
arc-minute of error); sidereal longitudes use the Lahiri ayanamsa. Checked
against drikpanchang.com's published dates for Hyderabad - see
tests/test_panchang.py.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from typing import Callable, Iterator, List, Optional

import ephem

IST = timezone(timedelta(hours=5, minutes=30))

MONTHS = [
    "Chaitra", "Vaishakha", "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada",
    "Ashvina", "Kartika", "Margashirsha", "Pausha", "Magha", "Phalguna",
]


def _ephem_date(moment: datetime) -> ephem.Date:
    return ephem.Date(moment.astimezone(timezone.utc).replace(tzinfo=None))


def _to_ist(value: ephem.Date) -> datetime:
    return value.datetime().replace(tzinfo=timezone.utc).astimezone(IST)


def _longitudes(moment: datetime) -> tuple[float, float]:
    """Tropical ecliptic longitudes (degrees) of the sun and moon."""
    when = _ephem_date(moment)
    sun, moon = ephem.Sun(when), ephem.Moon(when)
    sun_lon = math.degrees(ephem.Ecliptic(sun, epoch=when).lon)
    moon_lon = math.degrees(ephem.Ecliptic(moon, epoch=when).lon)
    return sun_lon, moon_lon


def _elongation(moment: datetime) -> float:
    sun_lon, moon_lon = _longitudes(moment)
    return (moon_lon - sun_lon) % 360


def tithi_at(moment: datetime) -> int:
    """1-30: 1-15 Shukla Pratipada..Purnima, 16-30 Krishna Pratipada..Amavasya."""
    return int(_elongation(moment) // 12) + 1


def lahiri_ayanamsa(moment: datetime) -> float:
    """Lahiri (Chitrapaksha) ayanamsa in degrees - linear precession from its
    J2000 value, accurate to a few arc-seconds over this century."""
    years = (moment - datetime(2000, 1, 1, 12, tzinfo=timezone.utc)).total_seconds() / (365.25 * 86400)
    return 23.85306 + years * (50.2788 / 3600)


def sidereal_sun(moment: datetime) -> float:
    sun_lon, _ = _longitudes(moment)
    return (sun_lon - lahiri_ayanamsa(moment)) % 360


def rasi_of_sun(moment: datetime) -> int:
    """0 Mesha .. 11 Meena."""
    return int(sidereal_sun(moment) // 30)


def _bisect(lo: datetime, hi: datetime, is_after: Callable[[datetime], bool]) -> datetime:
    """The moment in (lo, hi] where is_after flips to True (to ~1 second)."""
    while (hi - lo).total_seconds() > 1:
        mid = lo + (hi - lo) / 2
        if is_after(mid):
            hi = mid
        else:
            lo = mid
    return hi


def new_moons(start: datetime, end: datetime) -> List[datetime]:
    """Every new moon (sun-moon conjunction) between start and end."""
    found, step = [], timedelta(hours=12)
    moment, prev = start, _elongation(start)
    while moment < end:
        nxt = moment + step
        cur = _elongation(nxt)
        if cur < prev:  # wrapped past 360 -> conjunction inside this step
            found.append(_bisect(moment, nxt, lambda t: _elongation(t) < 180))
        moment, prev = nxt, cur
    return found


@dataclass(frozen=True)
class LunarMonth:
    name: str          # Chaitra .. Phalguna
    adhika: bool       # an extra month - the sun changes no sign during it
    start: datetime    # the new moon that begins it (IST)
    end: datetime      # the next new moon


def lunar_months(start: date, end: date) -> List[LunarMonth]:
    """Every amanta lunar month overlapping start..end."""
    moons = new_moons(datetime.combine(start - timedelta(days=62), datetime.min.time(), IST),
                      datetime.combine(end + timedelta(days=62), datetime.min.time(), IST))
    months = []
    for begin, finish in zip(moons, moons[1:]):
        rasi = rasi_of_sun(begin)
        months.append(LunarMonth(
            name=MONTHS[(rasi + 1) % 12],
            adhika=rasi == rasi_of_sun(finish),
            start=begin.astimezone(IST),
            end=finish.astimezone(IST),
        ))
    return months


# ------------------------------------------------------------------ the day
@dataclass(frozen=True)
class Place:
    latitude: float
    longitude: float
    elevation: float = 0.0


@lru_cache(maxsize=4096)
def _rise_set(place: Place, day: date, body: str, event: str) -> Optional[datetime]:
    """First sunrise/sunset/moonrise at `place` during the IST civil day `day`."""
    observer = ephem.Observer()
    observer.lat, observer.lon = str(place.latitude), str(place.longitude)
    observer.elevation = place.elevation
    observer.pressure = 0  # no refraction model; horizon below compensates
    observer.horizon = "-0:34"
    observer.date = _ephem_date(datetime.combine(day, datetime.min.time(), IST))
    target = ephem.Sun() if body == "sun" else ephem.Moon()
    try:
        found = observer.next_rising(target) if event == "rise" else observer.next_setting(target)
    except (ephem.AlwaysUpError, ephem.NeverUpError):
        return None
    moment = _to_ist(found)
    return moment if moment.date() == day else None


def sunrise(place: Place, day: date) -> datetime:
    return _rise_set(place, day, "sun", "rise")


def sunset(place: Place, day: date) -> datetime:
    return _rise_set(place, day, "sun", "set")


# When on a civil day a festival's tithi must prevail - a window of that day
# (a zero-length one for a moment such as sunrise). The daytime (sunrise to
# sunset) is split into five equal parts - pratah, sangava, madhyahna,
# aparahna, sayahna - or two halves, purvahna and aparahna.
Window = tuple[datetime, datetime]


def _day_fraction(a: float, b: float) -> Callable[[Place, date], Window]:
    def window(place: Place, day: date) -> Window:
        rise, sset = sunrise(place, day), sunset(place, day)
        return rise + (sset - rise) * a, rise + (sset - rise) * b
    return window


def _moment(at: Callable[[Place, date], datetime]) -> Callable[[Place, date], Window]:
    return lambda place, day: (at(place, day), at(place, day))


def _night_middle(place: Place, day: date) -> datetime:
    sset = sunset(place, day)
    return sset + (sunrise(place, day + timedelta(days=1)) - sset) / 2


def _moonrise(place: Place, day: date) -> datetime:
    # No moonrise on this civil day (it rose just after midnight the next
    # day): judge by late evening instead.
    return _rise_set(place, day, "moon", "rise") or sunset(place, day) + timedelta(hours=5)


KALA: dict[str, Callable[[Place, date], Window]] = {
    "sunrise": _moment(sunrise),
    "purvahna": _day_fraction(0, 0.5),
    "madhyahna": _day_fraction(0.4, 0.6),
    "aparahna": _day_fraction(0.6, 0.8),
    "pradosh": lambda place, day: (sunset(place, day), sunset(place, day) + timedelta(minutes=144)),
    "nishita": lambda place, day: (_night_middle(place, day) - timedelta(minutes=24),
                                   _night_middle(place, day) + timedelta(minutes=24)),
    "moonrise": _moment(_moonrise),
}


def tithi_span(month: LunarMonth, tithi: int) -> Window:
    """When `tithi` of `month` begins and ends."""
    # Within a lunar month the elongation climbs steadily from 0 to 360 degrees
    # (it's ~0 right at the new moon, so start looking an hour in).
    def find(target: float) -> datetime:
        if target == 0:
            return month.start
        if target >= 360:
            return month.end
        reached = lambda moment: _elongation(moment) >= target  # noqa: E731
        lo = month.start + timedelta(hours=1)
        while not reached(lo + timedelta(hours=6)):
            lo += timedelta(hours=6)
        return _bisect(lo, lo + timedelta(hours=6), reached).astimezone(IST)

    return find((tithi - 1) * 12.0), find(tithi * 12.0)


TRI_MUHURTA = timedelta(minutes=144)  # three muhurtas of 48 minutes


def observance_day(place: Place, month: LunarMonth, tithi: int, kala: str) -> date:
    """The first civil day on which `tithi` of `month` prevails during `kala`.
    A tithi that touches no such window is observed on the day at whose
    sunrise it prevails (or, if none - it began and ended between two
    sunrises - the day it began).

    "purvahna" (morning) festivals follow the three-muhurta rule instead: the
    day at whose sunrise the tithi prevails if it lasts at least three
    muhurtas past that sunrise, else the day before."""
    begin, finish = tithi_span(month, tithi)
    days = list(iter_days(begin.date() - timedelta(days=1), finish.date()))
    udaya = next((d for d in days if begin <= sunrise(place, d) < finish), None)
    if kala == "purvahna" and udaya:
        return udaya if finish - sunrise(place, udaya) >= TRI_MUHURTA else udaya - timedelta(days=1)
    window = KALA[kala]
    for day in days:
        a, b = window(place, day)
        if (begin <= a < finish) if a == b else (a < finish and begin < b):
            return day
    return udaya or begin.date()


def sankranti(rasi: int, near: date) -> datetime:
    """When the sun enters sidereal sign `rasi` (0 Mesha .. 11 Meena), within
    a month either side of `near`."""
    target = rasi * 30.0
    lo = datetime.combine(near - timedelta(days=35), datetime.min.time(), IST)
    hi = lo + timedelta(days=70)

    def passed(moment: datetime) -> bool:
        return (sidereal_sun(moment) - target) % 360 < 180

    # step to bracket the crossing, then bisect
    step = timedelta(days=1)
    moment = lo
    while moment < hi and passed(moment):
        moment += step  # skip the tail of the previous crossing, if any
    while moment < hi and not passed(moment + step):
        moment += step
    return _bisect(moment, moment + step, passed).astimezone(IST)


def iter_days(start: date, end: date) -> Iterator[date]:
    day = start
    while day <= end:
        yield day
        day += timedelta(days=1)
