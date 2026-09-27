"""N+1 guard: every list endpoint must run the same number of SQL statements
whether there's a handful of rows or several times as many. A relationship
read per row while serializing (e.g. donation.donor without joinedload) makes
the count grow with the data, and fails here."""
from datetime import date, time, timedelta

import pytest
from sqlalchemy import event

from app.core import cache as content_cache
from app.models.announcement import Announcement
from app.models.audit_log import AuditLog
from app.models.contact import ContactMessage
from app.models.donation import Donation
from app.models.donor import Donor
from app.models.festival import Festival
from app.models.finance import ExpenseCategory, ExpenseTransaction, IncomeSourceType, IncomeTransaction, PaymentMode
from app.models.gallery import Gallery
from app.models.member import Member
from app.models.pooja import Pooja
from app.models.seva_ticket import PaymentStatus, SevaTicket
from app.models.temple import Temple
from app.models.temple_timing import TempleTiming
from app.models.user import User

TODAY = date.today()
ROWS = 3

LIST_ENDPOINTS = [
    # "{seva}": the blessing seva created for the test - see below
    f"/api/v1/poojas/{{seva}}/calendar?start={TODAY - timedelta(days=182)}&end={TODAY + timedelta(days=182)}",
    f"/api/v1/poojas/{{seva}}/calendar/{TODAY}",
    "/api/v1/announcements",
    "/api/v1/announcements/admin/all",
    "/api/v1/audit-logs",
    "/api/v1/auth/admin/users",
    "/api/v1/contacts",
    "/api/v1/donations",
    "/api/v1/donors",
    "/api/v1/festivals",
    "/api/v1/festivals/admin/all",
    "/api/v1/finance/ledger",
    "/api/v1/finance/summary",
    "/api/v1/gallery",
    "/api/v1/gallery/admin/all",
    "/api/v1/meta/activity",
    "/api/v1/meta/stats",
    "/api/v1/poojas",
    "/api/v1/poojas/admin/all",
    "/api/v1/public/committee",
    "/api/v1/public/home",
    "/api/v1/seva-tickets",
    "/api/v1/seva-tickets/mine",
    "/api/v1/temple/timings/all",
    "/api/v1/temple-members",
]


def _seed_batch(db, batch: int, owner_id: int, blessing_seva_id: int) -> None:
    """ROWS more of everything, each row linked to a different staff user /
    donor / pooja, so any per-row relationship load shows up as extra queries."""
    staff = [User(username=f"staff{batch}-{i}", email=f"s{batch}-{i}@example.com", hashed_password="x",
                  roles=["STAFF"]) for i in range(ROWS)]
    poojas = [Pooja(name=f"Seva {batch}-{i}", pooja_type="daily") for i in range(ROWS)]
    donors = [Donor(name=f"Donor {batch}-{i}") for i in range(ROWS)]
    festival = Festival(name=f"Festival {batch}", festival_date=TODAY)
    db.add_all([*staff, *poojas, *donors, festival])
    db.flush()
    for i in range(ROWS):
        db.add_all([
            SevaTicket(ticket_number=f"T-{batch}-{i}", seva_id=poojas[i].id, seva_name=poojas[i].name,
                       devotee_name="Devotee", mobile_number="9876543210", seva_date=TODAY,
                       qr_token=f"qr-{batch}-{i}", booked_by_user_id=owner_id, created_by_admin_id=staff[i].id),
            Donation(donor_id=donors[i].id, amount=100, recorded_by_id=staff[i].id),
            Member(name=f"Member {batch}-{i}", phone="9876543210", show_on_website=True, user_id=staff[i].id),
            Announcement(title=f"News {batch}-{i}", created_by_id=staff[i].id, source_festival_id=festival.id),
            Gallery(title=f"Photo {batch}-{i}", image_url="https://example.com/p.jpg", category="TEMPLE",
                    created_by=staff[i].id),
            ContactMessage(name="Visitor", email="v@example.com", subject="Hello", message="Namaste"),
            IncomeTransaction(source_type=IncomeSourceType.DONATION, amount=100, payment_mode=PaymentMode.CASH,
                              received_by=staff[i].id),
            ExpenseTransaction(category=list(ExpenseCategory)[0], description="Flowers", amount=50,
                               payment_mode=PaymentMode.CASH, paid_to="Vendor", approved_by=staff[i].id),
            AuditLog(actor_id=staff[i].id, actor_username=staff[i].username, action="UPDATE", entity_type="pooja"),
            SevaTicket(ticket_number=f"B-{batch}-{i}", seva_id=blessing_seva_id, seva_name="Abhishekam",
                       devotee_name="Devotee", mobile_number="9876543210", seva_date=TODAY,
                       qr_token=f"bqr-{batch}-{i}", payment_status=PaymentStatus.PAID, amount=700,
                       occasion="Birthday", photo_url="https://example.com/p.jpg", show_publicly=True),
            TempleTiming(label=f"Darshan {batch}-{i}", start_time=time(6), end_time=time(12)),
        ])
    db.commit()


@pytest.fixture()
def query_counter(db):
    counter = {"n": 0}

    def count(*_args, **_kwargs):
        counter["n"] += 1

    engine = db.get_bind()
    event.listen(engine, "before_cursor_execute", count)
    yield counter
    event.remove(engine, "before_cursor_execute", count)


@pytest.mark.parametrize("url", LIST_ENDPOINTS)
def test_list_endpoint_query_count_does_not_grow_with_rows(client, db, super_admin, make_user, query_counter, url):
    _, admin_headers = super_admin
    devotee, devotee_headers = make_user("GENERAL_USER", username="devotee")
    headers = devotee_headers if url.endswith("/mine") else admin_headers
    db.add(Temple(name="SVVD"))
    seva = Pooja(name="Abhishekam", pooja_type="daily", is_paid=True, suggested_amount=700,
                 daily_slot_cap=7, public_blessings=True)
    db.add(seva)
    db.commit()
    url = url.replace("{seva}", str(seva.id))
    _seed_batch(db, 0, devotee.id, seva.id)

    def queries_for_request() -> int:
        content_cache._cache.clear()  # measure the database work, not a cached response
        query_counter["n"] = 0
        r = client.get(url, headers=headers)
        assert r.status_code == 200, r.text
        return query_counter["n"]

    few = queries_for_request()
    for batch in (1, 2, 3):
        _seed_batch(db, batch, devotee.id, seva.id)
    assert queries_for_request() == few
