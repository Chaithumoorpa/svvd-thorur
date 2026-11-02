"""Seeds a throwaway demo database with fictional temple data through the running API.

Setup (from backend/, in a scratch folder outside the repo):
  DATABASE_URL=sqlite:///<scratch>/demo.db SECRET_KEY=demo ENV=development
  python demo_seed.py init <scratch>        # creates tables + a demoadmin user, writes <scratch>/cred.txt
  uvicorn app.main:app --port 8001          # same env vars
  python demo_seed.py seed <scratch>        # loads content via http://localhost:8001/api/v1
"""
import datetime as dt
import secrets
import sys

mode, SP = sys.argv[1], sys.argv[2]

if mode == "init":
    from app.core.database import SessionLocal, engine
    from app.core.security import hash_password
    from app.models.base import Base
    import app.models  # noqa: F401  (registers every table)
    from app.models.user import User

    Base.metadata.create_all(engine)
    pw = "Demo-" + secrets.token_urlsafe(9)
    db = SessionLocal()
    db.add(User(username="demoadmin", hashed_password=hash_password(pw), roles=["SUPER_ADMIN"], is_active=True, must_change_password=False))
    db.commit()
    open(SP + "/cred.txt", "w").write(pw)
    print("initialised")
    sys.exit()

if mode == "blessings":
    from app.core.database import SessionLocal
    import app.models  # noqa: F401
    from app.models.pooja import Pooja
    from app.models.seva_ticket import SevaTicket

    db = SessionLocal()
    seva = db.query(Pooja).filter(Pooja.name == "Abhishekam").one()
    rows = db.query(SevaTicket).filter(SevaTicket.seva_id == seva.id).all()
    for t, (name, occasion) in zip(rows, [("R. Anitha", "Birthday"), ("S. Venkatesh", "Wedding Anniversary")]):
        t.seva_date, t.occasion, t.show_publicly = dt.date.today(), occasion, True
        t.review_status, t.devotee_name, t.payment_status = "APPROVED", name, "PAID"
    db.commit()
    print("blessings ready")
    sys.exit()

import httpx

c =httpx.Client(base_url="http://localhost:8001/api/v1", timeout=30)
c.headers["Authorization"] = "Bearer " + c.post("/auth/login", json={"username": "demoadmin", "password": open(SP + "/cred.txt").read()}).json()["access_token"]


def post(path, body, method="post"):
    r = getattr(c, method)(path, json=body)
    if r.status_code >= 300:
        print("FAIL", path, r.status_code, r.text[:200])
    return r.json() if r.status_code < 300 else {}


today = dt.date.today()
post("/temple", dict(name="Sri Varasidhi Vinayaka Swamy Temple", deity_name="Sri Varasidhi Vinayaka Swamy", tagline="Abode of blessings in Thorur",
                     history="A centuries-old shrine in Thorur, Mahabubabad district.", address="Main Road, Thorur", village="Thorur",
                     district="Mahabubabad", state="Telangana", pincode="506163", contact_phone="9876543210", contact_email="info@example.org"), "put")
for lab, s, e, note in [("Suprabhatam", "05:30", "06:00", "Morning awakening"), ("Morning Darshan", "06:00", "12:30", None), ("Evening Darshan", "16:00", "20:30", "Aarti at 19:00")]:
    post("/temple/timings", dict(label=lab, start_time=s, end_time=e, days="Daily", note=note))
ids = {}
for i, (n, d, t, paid, amt, bless) in enumerate([
        ("Nitya Pooja", "Daily worship of the deity", "daily", False, None, False), ("Ganapati Homam", "Homam for removal of obstacles", "special", True, 501, False),
        ("Abhishekam", "Sacred bathing of the deity with milk, honey and sandal", "special", True, 251, True), ("Archana", "Chanting of the 108 names", "daily", True, 51, False),
        ("Vinayaka Chavithi Special Seva", "Annual festival seva", "festival", True, 1116, False)]):
    ids[n] = post("/poojas", dict(name=n, description=d, pooja_type=t, is_paid=paid, suggested_amount=amt, sort_order=i, start_time="07:00", end_time="08:00", public_blessings=bless)).get("id")
for n, days, desc in [("Vinayaka Chavithi", 34, "Ten-day celebration with daily abhishekam and annadanam"), ("Sankashti Chaturthi", 12, "Monthly vow dedicated to Lord Ganesha"),
                      ("Maha Shivaratri", 120, "Night-long vigil and abhishekam"), ("Ugadi", 160, "Telugu new year celebrations")]:
    post("/festivals", dict(name=n, festival_date=str(today + dt.timedelta(days=days)), description=desc, location="Temple premises", auto_announce=False))
for t, m in [("Annadanam every Saturday", "Free meals for devotees at 12:30 PM in the temple hall."), ("Darshan timings update", "Evening darshan now extended until 8:30 PM."),
             ("Vinayaka Chavithi preparations", "Volunteers are invited to register with the temple office.")]:
    post("/announcements", dict(title=t, message=m, start_date=str(today)))
for i, (t, img) in enumerate([("Sri Varasidhi Vinayaka", "varasidhi"), ("Sri Maha Vishnu", "vishnu"), ("Goddess Durga", "durga"), ("Dakshinamurthy", "dakshinamurthy")]):
    post("/gallery", dict(title=t, image_url=f"/deities/{img}.png", category="TEMPLE", sort_order=i))
for i, (n, ph, pos) in enumerate([("K. Ramesh Reddy", "9000000001", "President"), ("P. Lakshmi Narayana", "9000000002", "Secretary"), ("S. Venkata Rao", "9000000003", "Treasurer"), ("Pandit M. Srinivas", "9000000004", "Chief Priest")]):
    post("/temple-members", dict(name=n, phone=ph, position=pos, show_on_website=True, sort_order=i))
for (n, ph), (amt, ty, pm) in zip([("A. Suresh", "9100000001"), ("B. Padmavathi", "9100000002"), ("C. Narasimha Rao", "9100000003")],
                                  [(5001, "festival", "UPI"), (1116, "annadanam", "CASH"), (25000, "construction", "BANK")]):
    d = post("/donors", dict(name=n, phone=ph))
    dn = post("/donations", dict(donor_id=d["id"], amount=amt, donation_type=ty, payment_mode=pm, purpose="Temple seva"))
    if dn and ty != "annadanam":
        post(f"/donations/{dn['id']}/receipt", {})
for n, ph, seva, st in [("R. Anitha", "9200000001", "Abhishekam", "PAID"), ("T. Mahesh", "9200000002", "Ganapati Homam", "PAID"), ("V. Sandhya", "9200000003", "Archana", "PENDING"), ("G. Kiran", "9200000004", "Nitya Pooja", "FREE")]:
    amt = {"Abhishekam": 251, "Ganapati Homam": 501, "Archana": 51}.get(seva, 0)
    post("/seva-tickets/admin", dict(seva_id=ids[seva], devotee_name=n, mobile_number=ph, seva_date=str(today + dt.timedelta(days=1)), payment_status=st, amount=amt))
post("/contacts", dict(name="Devotee Guest", email="guest@example.org", subject="Seva timing", message="What time does the evening abhishekam start?"))

# Public blessings only come from online bookings (email OTP) that staff approve, so for the demo
# mark two of today's Abhishekam tickets as approved directly in the throwaway database instead.
print("seeded - now run: python demo_seed.py blessings", SP)
