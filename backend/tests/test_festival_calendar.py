"""The computed festival calendar, checked against drikpanchang.com's
published dates for Hyderabad (the nearest city it lists to Thorur) for two
whole years, plus how the daily fill treats the festivals table."""
from datetime import date

import pytest

from app.models.festival import Festival
from app.repositories.festival_repo import FestivalRepository
from app.services.festival_calendar import FestivalCalendarService, occurrences
from app.services.panchang import Place, lunar_months

HYDERABAD = Place(17.3839, 78.4561, 515)

PUBLISHED = {
    2026: {
        "sankashti-chaturthi": ["01-06", "02-05", "03-06", "04-05", "05-05", "06-03", "07-03", "08-02",
                                "08-31", "09-29", "10-29", "11-27", "12-26"],
        "vinayaka-chaturthi": ["01-22", "02-21", "03-22", "04-20", "05-20", "06-18", "07-17", "08-16",
                               "09-14", "10-14", "11-13", "12-13"],
        "makara-sankranti": ["01-14"], "vasant-panchami": ["01-23"], "ratha-saptami": ["01-25"],
        "maha-shivaratri": ["02-15"], "ugadi": ["03-19"], "sri-rama-navami": ["03-26"],
        "akshaya-tritiya": ["04-19"], "guru-purnima": ["07-29"], "varalakshmi-vratam": ["08-28"],
        "krishna-janmashtami": ["09-04"], "ganesh-chaturthi": ["09-14"], "devi-navaratri": ["10-11"],
        "vijayadashami": ["10-20"], "deepavali": ["11-08"], "nagula-chavithi": ["11-13"],
        "karthika-purnima": ["11-24"], "vaikuntha-ekadashi": ["12-20"],
    },
    2027: {
        "sankashti-chaturthi": ["01-25", "02-24", "03-25", "04-24", "05-23", "06-22", "07-22", "08-20",
                                "09-19", "10-18", "11-17", "12-16"],
        "makara-sankranti": ["01-15"], "vasant-panchami": ["02-11"], "ratha-saptami": ["02-13"],
        "maha-shivaratri": ["03-06"], "ugadi": ["04-07"], "sri-rama-navami": ["04-15"],
        "akshaya-tritiya": ["05-09"], "guru-purnima": ["07-18"], "varalakshmi-vratam": ["08-13"],
        "krishna-janmashtami": ["08-25"], "ganesh-chaturthi": ["09-04"],
    },
}
VINAYAKA_2027_JAN_TO_SEP = ["01-11", "02-10", "03-12", "04-10", "05-09", "06-08", "07-07", "08-05", "09-04"]


def _by_rule(year):
    found = {}
    for o in occurrences(date(year, 1, 1), date(year, 12, 31), HYDERABAD):
        found.setdefault(o.key.split(":")[0], []).append(o)
    return found


@pytest.mark.parametrize("year", sorted(PUBLISHED))
def test_dates_match_the_published_panchang(year):
    found = _by_rule(year)
    got = {rule: [o.start.strftime("%m-%d") for o in found.get(rule, [])] for rule in PUBLISHED[year]}
    assert got == PUBLISHED[year]


def test_vinayaka_chaturthi_2027():
    got = [o.start.strftime("%m-%d") for o in _by_rule(2027)["vinayaka-chaturthi"]]
    assert got[:9] == VINAYAKA_2027_JAN_TO_SEP


def test_ganesh_navaratri_runs_to_ananta_chaturdashi():
    [ganesh] = _by_rule(2026)["ganesh-chaturthi"]
    assert (ganesh.start, ganesh.end) == (date(2026, 9, 14), date(2026, 9, 25))


def test_2026_has_an_adhika_jyeshtha_and_no_annual_festival_in_it():
    months = lunar_months(date(2026, 5, 1), date(2026, 6, 30))
    adhika = [m for m in months if m.adhika]
    assert [m.name for m in adhika] == ["Jyeshtha"]
    monthly = [o.name for o in occurrences(date(2026, 5, 17), date(2026, 6, 14), HYDERABAD)]
    assert "Sankashti Chaturthi (Adhika Jyeshtha)" in monthly


# ------------------------------------------------------------------ the fill


def test_fill_adds_a_year_once(db):
    service = FestivalCalendarService(FestivalRepository(db))
    added = service.fill(today=date(2026, 9, 27))
    names = {f.name for f in added}
    assert {"Sankashti Chaturthi (Ashvina)", "Deepavali", "Ugadi", "Maha Shivaratri"} <= names
    assert all(date(2026, 9, 27) <= f.festival_date <= date(2027, 9, 27) for f in added)
    assert service.fill(today=date(2026, 9, 27)) == []  # idempotent
    assert len(service.fill(today=date(2026, 10, 27))) > 0  # rolls forward a month


def test_fill_never_touches_a_row_an_admin_edited_or_hid(db):
    service = FestivalCalendarService(FestivalRepository(db))
    service.fill(today=date(2026, 9, 27))
    deepavali = db.query(Festival).filter(Festival.name == "Deepavali").one()
    deepavali.is_active = False
    sankashti = db.query(Festival).filter(Festival.source_key == "sankashti-chaturthi:2026-09-29").one()
    sankashti.description = "Our own words"
    db.commit()
    service.fill(today=date(2026, 9, 27))
    assert db.query(Festival).filter(Festival.name == "Deepavali").count() == 1
    db.refresh(deepavali), db.refresh(sankashti)
    assert (deepavali.is_active, sankashti.description) == (False, "Our own words")


def test_admin_can_fill_the_calendar_now(client, admin):
    _, headers = admin
    assert client.post("/api/v1/festivals/calendar/fill").status_code == 401
    r = client.post("/api/v1/festivals/calendar/fill", headers=headers)
    assert r.status_code == 200 and r.json()["added"] > 20
    public = client.get("/api/v1/festivals?upcoming=true").json()
    assert any(f["name"].startswith("Sankashti Chaturthi") and f["source_key"] for f in public)
