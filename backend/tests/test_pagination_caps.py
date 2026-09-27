"""Public list endpoints that used to be truly unbounded when their `limit`
query param was omitted (festivals, announcements) or had no cap at all
(poojas, a devotee's own seva tickets) are now bounded even by default, and
the public ones cache the response for a short time so repeat visitors
don't all hit the database. Existing behavior (an explicit smaller `limit`,
response shape) is unchanged - see test_content.py for that coverage."""
from datetime import date, timedelta

from app.models.pooja import Pooja
from app.models.seva_ticket import PaymentStatus, SevaTicket, TicketSource, TicketStatus
from app.repositories.pooja_repo import PoojaRepository
from app.repositories.seva_ticket_repo import SevaTicketRepository


def test_festival_list_still_honours_an_explicit_smaller_limit(client, admin):
    _, headers = admin
    for i in range(3):
        client.post("/api/v1/festivals/", headers=headers, json={"name": f"Festival {i}"})
    assert len(client.get("/api/v1/festivals/?limit=2").json()) == 2


def test_announcement_list_still_honours_an_explicit_smaller_limit(client, staff):
    _, headers = staff
    for i in range(3):
        client.post("/api/v1/announcements/", headers=headers, json={"title": f"News {i}"})
    assert len(client.get("/api/v1/announcements/?limit=1").json()) == 1


def test_public_lists_are_cacheable(client):
    for path in ("/api/v1/poojas/", "/api/v1/festivals/", "/api/v1/announcements/"):
        r = client.get(path)
        assert r.status_code == 200
        assert "max-age" in r.headers.get("Cache-Control", ""), path


def test_pooja_repo_get_all_respects_its_limit(db):
    repo = PoojaRepository(db)
    for i in range(3):
        db.add(Pooja(name=f"Pooja {i}", pooja_type="daily", is_paid=False, is_active=True))
    db.commit()
    assert len(repo.get_all(limit=2)) == 2
    assert len(repo.get_all()) == 3  # default cap (200) is well above 3


def test_seva_ticket_repo_get_by_user_respects_its_limit(db):
    pooja = Pooja(name="Archana", pooja_type="daily", is_paid=False, is_active=True)
    db.add(pooja)
    db.commit()
    db.refresh(pooja)
    from app.core.security import hash_password
    from app.models.user import User

    user = User(username="cap_test_user", hashed_password=hash_password("Password123"), roles=["GENERAL_USER"])
    db.add(user)
    db.commit()
    db.refresh(user)

    for i in range(3):
        db.add(SevaTicket(
            ticket_number=f"SVVD-2026-90{i:04d}", seva_id=pooja.id, seva_name=pooja.name,
            devotee_name="Devotee", mobile_number="9876543210", seva_date=date.today() + timedelta(days=i + 1),
            payment_status=PaymentStatus.FREE, amount=0, status=TicketStatus.ACTIVE,
            source=TicketSource.ONLINE, qr_token=f"cap-tok-{i}", booked_by_user_id=user.id,
        ))
    db.commit()

    repo = SevaTicketRepository(db)
    assert len(repo.get_by_user(user.id, limit=2)) == 2
    assert len(repo.get_by_user(user.id)) == 3  # default cap (200) is well above 3
