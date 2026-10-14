"""Official letters: drafting, signer-approved signatures, seal, issue/revoke,
verification, and the image cleaning that turns a photo into a transparent mark."""
import base64
from datetime import date
from io import BytesIO

import pytest
from PIL import Image, ImageDraw
from pypdf import PdfReader

from app.models.audit_log import AuditLog
from app.models.letter import LetterImageKind
from app.models.member import Member
from app.services.email_service import EmailService
from app.services.letter_image_service import clean_mark

TODAY = date.today().isoformat()


def _photo(ink=(25, 35, 120), paper=(236, 232, 224), size=(900, 400), fmt="JPEG") -> str:
    """A phone-like photo of a signature: greyish paper, blue scribble."""
    img = Image.new("RGB", size, paper)
    d = ImageDraw.Draw(img)
    d.line([(120, 260), (220, 120), (300, 280), (380, 140), (470, 250), (620, 170), (760, 230)], fill=ink, width=9)
    d.ellipse((560, 120, 700, 230), outline=ink, width=7)
    out = BytesIO()
    img.save(out, format=fmt)
    return f"data:image/{fmt.lower()};base64," + base64.b64encode(out.getvalue()).decode()


@pytest.fixture()
def mails(monkeypatch):
    sent = []
    monkeypatch.setattr(EmailService, "send", lambda self, to, subject, body, **style: sent.append((to, subject, body)) or True)
    return sent


@pytest.fixture()
def signer(db, make_user):
    """A committee member (President) with their own login."""
    user, headers = make_user("TRUSTEE", username="president", email="president@example.com")
    member = Member(name="K. Ramaiah", phone="9000000001", position="President", user_id=user.id)
    db.add(member)
    db.commit()
    return member, headers


@pytest.fixture()
def offline(db):
    """A member without a login - signs printed copies in ink."""
    member = Member(name="S. Lakshmi", phone="9000000002", position="Treasurer")
    db.add(member)
    db.commit()
    return member


def _letter(client, headers, signatories, **extra):
    body = {"kind": "APPOINTMENT", "letter_date": TODAY, "subject": "Appointment as Archaka",
            "recipient_name": "Sri Venkata Sharma", "recipient_address": "H.No 2-14\nThorur",
            "salutation": "Dear Sri Venkata Sharma,", "closing": "Yours sincerely,",
            "body": "We are pleased to appoint you as Archaka of the temple with effect from 1 November.",
            "signatories": signatories, **extra}
    r = client.post("/api/v1/letters", headers=headers, json=body)
    assert r.status_code == 201, r.text
    return r.json()


def test_clean_mark_makes_paper_transparent():
    raw = base64.b64decode(_photo().split(",", 1)[1])
    png, w, h, digest = clean_mark(raw, LetterImageKind.SIGNATURE)
    img = Image.open(BytesIO(png))
    assert img.mode == "RGBA" and (w, h) == img.size and len(digest) == 64
    assert w <= 900 and w > h                       # cropped to the scribble, scaled down
    assert img.getpixel((2, 2))[3] == 0             # the corner (paper) is transparent
    alphas = [px[3] for px in img.getdata()]
    assert max(alphas) == 255                       # the ink is solid
    r, g, b, _ = max(img.getdata(), key=lambda px: px[3])
    assert b > r and b > g                          # blue ink stays blue


def test_clean_mark_rejects_blank_and_non_images():
    blank = BytesIO()
    Image.new("RGB", (400, 200), (240, 240, 240)).save(blank, format="PNG")
    with pytest.raises(Exception) as e:
        clean_mark(blank.getvalue(), LetterImageKind.SIGNATURE)
    assert "No clear mark" in str(e.value.detail)
    with pytest.raises(Exception) as e:
        clean_mark(b"not an image", LetterImageKind.SEAL)
    assert "not an image" in str(e.value.detail)


def test_templates(client, admin):
    _, headers = admin
    rows = client.get("/api/v1/letters/templates", headers=headers).json()
    kinds = {t["kind"] for t in rows}
    assert {"GENERAL", "APPOINTMENT", "NOC", "SERVICE_CERTIFICATE", "DONATION_ACKNOWLEDGEMENT"} <= kinds
    noc = next(t for t in rows if t["kind"] == "NOC")
    assert noc["certificate_title"] == "NO OBJECTION CERTIFICATE" and "[Purpose" in noc["body"]


def test_full_workflow(client, admin, signer, offline, db, mails):
    admin_user, headers = admin
    member, signer_h = signer
    letter = _letter(client, headers, [{"member_id": member.id}, {"member_id": offline.id, "role": "ATTESTOR"}])
    assert letter["status"] == "DRAFT" and letter["reference_number"] is None
    assert [s["designation"] for s in letter["signatories"]] == ["President", "Treasurer"]
    assert letter["signatories"][0]["has_login"] and not letter["signatories"][1]["has_login"]

    # admin uploads the signer's signature; the signer is told by email
    r = client.put(f"/api/v1/letters/signatures/{member.id}", headers=headers, json={"image": _photo()})
    assert r.status_code == 200 and r.json()["has_signature"]
    assert mails and mails[-1][0] == "president@example.com" and "only when you sign" in mails[-1][2]

    r = client.post(f"/api/v1/letters/{letter['id']}/send", headers=headers)
    assert r.json()["status"] == "AWAITING_SIGNATURES"
    assert any("awaiting your signature" in m[1] for m in mails)

    # the admin cannot sign for the president; issuing waits for everyone
    r = client.post(f"/api/v1/letters/{letter['id']}/sign", headers=headers, json={"password": "Password123"})
    assert r.status_code == 403
    assert client.post(f"/api/v1/letters/{letter['id']}/issue", headers=headers).status_code == 409

    # the president sees it, can open the draft PDF, and signs with their password
    mine = client.get("/api/v1/letters/mine", headers=signer_h).json()
    assert mine["has_signature"] and [p["letter_id"] for p in mine["pending"]] == [letter["id"]]
    assert client.get(f"/api/v1/letters/{letter['id']}/pdf", headers=signer_h).status_code == 200
    r = client.post(f"/api/v1/letters/{letter['id']}/sign", headers=signer_h, json={"password": "wrong"})
    assert r.status_code == 400
    assert db.query(AuditLog).filter(AuditLog.action == "SIGN_FAILED").count() == 1
    r = client.post(f"/api/v1/letters/{letter['id']}/sign", headers=signer_h, json={"password": "Password123"})
    assert r.status_code == 200 and r.json()["signatories"][0]["status"] == "SIGNED"
    assert "You signed" in mails[-1][1] and "IST" in mails[-1][2]
    assert "IP" not in mails[-1][2] and "testclient" not in mails[-1][2]   # no IP address in emails
    assert client.get("/api/v1/letters/mine", headers=signer_h).json()["pending"] == []
    # a draft never carries the signature image - only the logo is embedded
    draft = PdfReader(BytesIO(client.get(f"/api/v1/letters/{letter['id']}/pdf", headers=headers).content)).pages[0]
    draft_text = " ".join(draft.extract_text().split())
    assert len(draft.images) == 1 and "shown when issued" in draft_text and "DRAFT" in draft_text

    # the treasurer has no login: marked as signing in ink
    slot = r.json()["signatories"][1]["id"]
    r = client.post(f"/api/v1/letters/{letter['id']}/signatories/{slot}/paper", headers=headers)
    assert r.json()["signatories"][1]["status"] == "PAPER"

    # seal is required when ticked
    assert "seal" in client.post(f"/api/v1/letters/{letter['id']}/issue", headers=headers).json()["detail"]
    seal = _photo(ink=(110, 40, 140), size=(500, 500), fmt="PNG")
    assert client.put("/api/v1/letters/seal", headers=headers, json={"image": seal}).json()["has_seal"]
    r = client.post(f"/api/v1/letters/{letter['id']}/issue", headers=headers)
    issued = r.json()
    assert issued["status"] == "ISSUED"
    assert issued["reference_number"] == f"SVVD/{date.today().year}/0001"
    assert issued["verify_url"].endswith("/letters/verify/" + issued["verify_url"].rsplit("/", 1)[-1])

    # the PDF: letterhead, reference, both names, verification link, no DRAFT
    pdf = client.get(f"/api/v1/letters/{letter['id']}/pdf", headers=headers)
    assert pdf.headers["content-type"] == "application/pdf"
    text = "".join(p.extract_text() for p in PdfReader(BytesIO(pdf.content)).pages)
    for expected in (issued["reference_number"], "K. Ramaiah", "S. Lakshmi", "ATTESTED BY", "Subject: Appointment",
                     "Verify this letter", "Digitally signed on"):
        assert expected in text, expected
    assert "DRAFT" not in text

    # public verification - no login
    token = issued["verify_url"].rsplit("/", 1)[-1]
    v = client.get(f"/api/v1/letters/verify/{token}").json()
    assert v["status"] == "ISSUED" and v["reference_number"] == issued["reference_number"]
    assert [(s["name"], s["method"]) for s in v["signatories"]] == [("K. Ramaiah", "digital"), ("S. Lakshmi", "ink")]
    assert "body" not in v

    # replacing the signature later doesn't change the issued letter
    client.put(f"/api/v1/letters/signatures/{member.id}", headers=headers, json={"image": _photo(ink=(10, 10, 10))})
    assert client.get(f"/api/v1/letters/{letter['id']}/pdf", headers=headers).status_code == 200

    # issued letters can't be edited or deleted, only revoked
    assert client.delete(f"/api/v1/letters/{letter['id']}", headers=headers).status_code == 409
    r = client.post(f"/api/v1/letters/{letter['id']}/revoke", headers=headers, json={"reason": "Issued in error"})
    assert r.json()["status"] == "REVOKED"
    v = client.get(f"/api/v1/letters/verify/{token}").json()
    assert v["status"] == "REVOKED" and v["revoke_reason"] == "Issued in error"
    text = PdfReader(BytesIO(client.get(f"/api/v1/letters/{letter['id']}/pdf", headers=headers).content)).pages[0]
    assert "REVOKED" in text.extract_text()
    actions = {a for (a,) in db.query(AuditLog.action).filter(AuditLog.entity_type == "letter").all()}
    assert {"CREATE", "SEND", "SIGN", "SIGN_FAILED", "MARK_PAPER", "ISSUE", "REVOKE"} <= actions


def test_signing_needs_a_signature_on_file(client, admin, signer):
    _, headers = admin
    member, signer_h = signer
    letter = _letter(client, headers, [{"member_id": member.id}], include_seal=False)
    client.post(f"/api/v1/letters/{letter['id']}/send", headers=headers)
    r = client.post(f"/api/v1/letters/{letter['id']}/sign", headers=signer_h, json={"password": "Password123"})
    assert r.status_code == 409 and "upload one" in r.json()["detail"]
    # the signer can upload their own
    r = client.put("/api/v1/letters/mine/signature", headers=signer_h, json={"image": _photo()})
    assert r.status_code == 200 and r.json()["has_signature"]
    assert client.get("/api/v1/letters/mine/signature.png", headers=signer_h).headers["content-type"] == "image/png"
    r = client.post(f"/api/v1/letters/{letter['id']}/sign", headers=signer_h, json={"password": "Password123"})
    assert r.status_code == 200
    r = client.post(f"/api/v1/letters/{letter['id']}/issue", headers=headers)
    assert r.status_code == 200 and r.json()["reference_number"].endswith("/0001")


def test_placeholders_block_sending_and_recall_clears_signatures(client, admin, signer, offline):
    _, headers = admin
    member, signer_h = signer
    client.put(f"/api/v1/letters/signatures/{member.id}", headers=headers, json={"image": _photo()})
    letter = _letter(client, headers, [{"member_id": member.id}], body="Appointed as [Designation] from today on.")
    r = client.post(f"/api/v1/letters/{letter['id']}/send", headers=headers)
    assert r.status_code == 400 and "[Designation]" in r.json()["detail"]

    fixed = {**{k: letter[k] for k in ("kind", "letter_date", "subject", "recipient_name", "recipient_address",
                                       "salutation", "closing", "include_seal")},
             "body": "Appointed as Archaka from today on.", "signatories": [{"member_id": member.id}]}
    assert client.put(f"/api/v1/letters/{letter['id']}", headers=headers, json=fixed).status_code == 200
    client.post(f"/api/v1/letters/{letter['id']}/send", headers=headers)
    assert client.put(f"/api/v1/letters/{letter['id']}", headers=headers, json=fixed).status_code == 409
    client.post(f"/api/v1/letters/{letter['id']}/sign", headers=signer_h, json={"password": "Password123"})
    r = client.post(f"/api/v1/letters/{letter['id']}/recall", headers=headers)
    assert r.json()["status"] == "DRAFT" and r.json()["signatories"][0]["status"] == "PENDING"
    assert client.delete(f"/api/v1/letters/{letter['id']}", headers=headers).status_code == 204


def test_decline_and_validation(client, admin, signer, offline):
    _, headers = admin
    member, signer_h = signer
    letter = _letter(client, headers, [{"member_id": member.id}], include_seal=False)
    client.post(f"/api/v1/letters/{letter['id']}/send", headers=headers)
    r = client.post(f"/api/v1/letters/{letter['id']}/decline", headers=signer_h, json={"reason": "Wrong date"})
    assert r.json()["signatories"][0]["status"] == "DECLINED"
    assert "Still waiting" in client.post(f"/api/v1/letters/{letter['id']}/issue", headers=headers).json()["detail"]

    bad = client.post("/api/v1/letters", headers=headers, json={
        "kind": "GENERAL", "letter_date": TODAY, "subject": "తెలుగు", "body": "Some body text here.",
        "signatories": []})
    assert bad.status_code == 422 and "English script" in bad.text
    dup = client.post("/api/v1/letters", headers=headers, json={
        "kind": "GENERAL", "letter_date": TODAY, "subject": "Hello", "body": "Some body text here.",
        "signatories": [{"member_id": offline.id}, {"member_id": offline.id}]})
    assert dup.status_code == 422
    assert client.post(f"/api/v1/letters/{letter['id']}/send", headers=headers).status_code == 409


def test_other_users_cannot_see_or_sign(client, admin, signer, make_user):
    _, headers = admin
    member, _ = signer
    letter = _letter(client, headers, [{"member_id": member.id}])
    _, stranger = make_user("STAFF", username="stranger")
    assert client.get(f"/api/v1/letters/{letter['id']}", headers=stranger).status_code == 403
    assert client.get(f"/api/v1/letters/{letter['id']}/pdf", headers=stranger).status_code == 403
    assert client.get("/api/v1/letters/mine", headers=stranger).json()["member_id"] is None
    r = client.put("/api/v1/letters/mine/signature", headers=stranger, json={"image": _photo()})
    assert r.status_code == 403
    # drafts are not verifiable
    assert client.get("/api/v1/letters/verify/not-a-real-token-123").status_code == 404


def test_linking_a_login_is_super_admin_only_and_retires_the_old_signature(client, admin, super_admin, offline,
                                                                          signer, make_user, db, mails):
    _, admin_h = admin
    _, root_h = super_admin
    member, _ = signer
    new_user, new_h = make_user("STAFF", username="lakshmi", email="lakshmi@example.com")
    url = f"/api/v1/letters/signatures/{offline.id}/login"
    assert client.put(url, headers=admin_h, json={"user_id": new_user.id}).status_code == 403

    r = client.put(url, headers=root_h, json={"user_id": new_user.id})
    assert r.status_code == 200 and r.json()["linked_username"] == "lakshmi" and r.json()["has_login"]
    assert any(m[0] == "lakshmi@example.com" and "linked" in m[1] for m in mails)
    assert client.get("/api/v1/letters/mine", headers=new_h).json()["member_id"] == offline.id
    log = db.query(AuditLog).filter(AuditLog.action == "LINK_LOGIN").one()
    assert log.changes == {"from": None, "to": "lakshmi"}

    # one login per member; same link again is a no-op error
    taken = client.put(url, headers=root_h, json={"user_id": member.user_id})
    assert taken.status_code == 409 and "K. Ramaiah" in taken.json()["detail"]
    assert client.put(url, headers=root_h, json={"user_id": new_user.id}).status_code == 409

    # moving the link away retires the signature uploaded for the previous login
    client.put("/api/v1/letters/mine/signature", headers=new_h, json={"image": _photo()})
    r = client.put(url, headers=root_h, json={"user_id": None})
    assert r.json()["has_signature"] is False and r.json()["linked_username"] is None


def test_wide_rubber_stamp_prints_at_full_width(client, admin, signer):
    from app.services.letter_pdf_service import WIDE_SEAL_W, _seal
    from reportlab.lib.units import mm
    wide = base64.b64decode(_photo(ink=(80, 40, 125), size=(1600, 320), fmt="PNG").split(",", 1)[1])
    png, *_ = clean_mark(wide, LetterImageKind.SEAL)
    img = _seal(png)
    assert img.drawWidth > 45 * mm and img.drawWidth <= WIDE_SEAL_W + 0.01
    ring = Image.new("RGB", (500, 500), (238, 236, 232))
    ImageDraw.Draw(ring).ellipse((40, 40, 460, 460), outline=(90, 40, 130), width=14)
    buf = BytesIO()
    ring.save(buf, format="PNG")
    png, *_ = clean_mark(buf.getvalue(), LetterImageKind.SEAL)
    assert _seal(png).drawWidth <= 30 * mm + 0.01


def test_authority_document_templates(client, admin, signer, offline):
    _, headers = admin
    member, _ = signer
    rows = {t["kind"]: t for t in client.get("/api/v1/letters/templates", headers=headers).json()}
    poa = rows["POWER_OF_ATTORNEY"]
    assert poa["certificate_title"] == "POWER OF ATTORNEY" and "[Attorney name]" in poa["body"]
    assert rows["RESOLUTION"]["certificate_title"] == "EXTRACT OF RESOLUTION" and "RESOLVED THAT" in rows["RESOLUTION"]["body"]
    assert rows["AUTHORISATION"]["certificate_title"] is None and rows["AUTHORISATION"]["closing"] == "Yours faithfully,"

    # unfilled template can't be sent; the PDF names the second group "WITNESSES"
    letter = _letter(client, headers, [{"member_id": member.id}, {"member_id": offline.id, "role": "ATTESTOR"}],
                     kind="POWER_OF_ATTORNEY", subject=poa["subject"], body=poa["body"])
    assert "[Attorney name]" in client.post(f"/api/v1/letters/{letter['id']}/send", headers=headers).json()["detail"]
    pages = PdfReader(BytesIO(client.get(f"/api/v1/letters/{letter['id']}/pdf", headers=headers).content)).pages
    text = " ".join(" ".join(p.extract_text() for p in pages).split())
    assert "POWER OF ATTORNEY" in text and "WITNESSES" in text and "ATTESTED BY" not in text
