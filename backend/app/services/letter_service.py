"""Official letters: drafting, collecting signatures, issuing, revoking, and the
signature / seal images that go on them. See app.models.letter for the rules."""
import logging
import secrets
from datetime import datetime
from typing import List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.config import settings
from app.core.pagination import PageParams, paginate
from app.core.security import verify_password
from app.models.letter import (
    LetterImage, LetterImageKind, LetterKind, LetterSignatory, LetterStatus, OfficialLetter, SignatoryRole,
    SignatoryStatus,
)
from app.models.member import Member
from app.models.temple import Temple
from app.models.user import User
from app.schemas.letter import LetterIn
from app.services.email_service import EmailService
from app.services.letter_image_service import MAX_UPLOAD_BYTES, clean_mark, decode_data_url
from app.services.letter_templates import LABELS, PLACEHOLDER, template_for

logger = logging.getLogger(__name__)

REFERENCE_PREFIX = "SVVD"
_EDITABLE = ("kind", "letter_date", "subject", "recipient_name", "recipient_address", "salutation", "body",
             "closing", "include_seal")
_DONE = (SignatoryStatus.SIGNED, SignatoryStatus.PAPER)


def verify_url(letter: OfficialLetter) -> str:
    return f"{settings.FRONTEND_BASE_URL}/letters/verify/{letter.verify_token}"


class LetterService:
    def __init__(self, db: Session, email: Optional[EmailService] = None):
        self.db = db
        self.email = email or EmailService()

    # ---- reading ----------------------------------------------------------------------------
    def _query(self):
        return self.db.query(OfficialLetter).options(
            selectinload(OfficialLetter.signatories).joinedload(LetterSignatory.member),
            joinedload(OfficialLetter.creator))

    def get(self, letter_id: int) -> OfficialLetter:
        letter = self._query().filter(OfficialLetter.id == letter_id).first()
        if not letter:
            raise HTTPException(status_code=404, detail="Letter not found")
        return letter

    def list(self, status: Optional[LetterStatus], q: Optional[str], params: PageParams):
        query = self._query()
        if status:
            query = query.filter(OfficialLetter.status == status)
        if q:
            like = f"%{q.strip()}%"
            query = query.filter(or_(OfficialLetter.subject.ilike(like), OfficialLetter.recipient_name.ilike(like),
                                     OfficialLetter.reference_number.ilike(like)))
        return paginate(query.order_by(OfficialLetter.id.desc()), params)

    def out(self, letter: OfficialLetter) -> dict:
        current = self._current_signature_members({s.member_id for s in letter.signatories if s.member_id})
        return {
            **{c: getattr(letter, c) for c in (
                "id", "reference_number", "kind", "status", "letter_date", "subject", "recipient_name",
                "recipient_address", "salutation", "body", "closing", "include_seal", "created_at", "sent_at",
                "issued_at", "revoked_at", "revoke_reason")},
            "created_by_name": letter.creator.username if letter.creator else None,
            "verify_url": verify_url(letter) if letter.reference_number else None,
            "signatories": [{
                "id": s.id, "member_id": s.member_id, "name": s.name, "designation": s.designation, "role": s.role,
                "status": s.status, "signed_at": s.signed_at, "decline_reason": s.decline_reason,
                "has_login": bool(s.member and s.member.user_id), "has_signature": s.member_id in current,
            } for s in letter.signatories],
        }

    def templates(self) -> List[dict]:
        temple = self._temple()
        name = temple.name if temple else "Sri Varasidhi Vinayaka Swamy Devasthanam"
        return [template_for(kind, name) for kind in LetterKind]

    # ---- drafting ---------------------------------------------------------------------------
    def create(self, data: LetterIn, user: User) -> OfficialLetter:
        letter = OfficialLetter(verify_token=secrets.token_urlsafe(18), status=LetterStatus.DRAFT, created_by=user.id,
                                **{f: getattr(data, f) for f in _EDITABLE})
        self.db.add(letter)
        self._set_signatories(letter, data)
        self.db.commit()
        return self.get(letter.id)

    def update(self, letter_id: int, data: LetterIn) -> OfficialLetter:
        letter = self.get(letter_id)
        self._require(letter, LetterStatus.DRAFT, "Only a draft can be edited - recall it to draft first")
        for f in _EDITABLE:
            setattr(letter, f, getattr(data, f))
        self._set_signatories(letter, data)
        self.db.commit()
        return self.get(letter.id)

    def _set_signatories(self, letter: OfficialLetter, data: LetterIn) -> None:
        ids = [s.member_id for s in data.signatories]
        members = {m.id: m for m in self.db.query(Member).filter(Member.id.in_(ids)).all()} if ids else {}
        letter.signatories.clear()
        self.db.flush()
        for order, s in enumerate(data.signatories):
            member = members.get(s.member_id)
            if not member or not member.is_active:
                raise HTTPException(status_code=400, detail="Signatories must be active committee members")
            letter.signatories.append(LetterSignatory(
                member_id=member.id, name=member.name, designation=s.designation or member.position, role=s.role,
                sort_order=order, status=SignatoryStatus.PENDING))

    def delete(self, letter_id: int) -> OfficialLetter:
        letter = self.get(letter_id)
        self._require(letter, LetterStatus.DRAFT, "Only a draft can be deleted - an issued letter can be revoked")
        self.db.delete(letter)
        self.db.commit()
        return letter

    # ---- signatures workflow ----------------------------------------------------------------
    def send(self, letter_id: int) -> OfficialLetter:
        letter = self.get(letter_id)
        self._require(letter, LetterStatus.DRAFT, "This letter has already been sent for signatures")
        if not letter.signatories:
            raise HTTPException(status_code=400, detail="Add at least one signatory")
        left = sorted({m for f in ("subject", "recipient_name", "recipient_address", "salutation", "body", "closing")
                       for m in PLACEHOLDER.findall(getattr(letter, f) or "")})
        if left:
            raise HTTPException(status_code=400, detail=f"Fill in the placeholders first: {', '.join(left[:6])}")
        letter.status = LetterStatus.AWAITING_SIGNATURES
        letter.sent_at = datetime.utcnow()
        self.db.commit()
        for s in letter.signatories:
            self._mail_member(s.member, f"Letter awaiting your signature: {letter.subject}", (
                f"A letter from {self._temple_name()} is waiting for your signature as {self._as(s)}.\n\n"
                f"Subject: {letter.subject}\n\n"
                f"Please sign in and review it at {settings.FRONTEND_BASE_URL}/sign-letters\n"
                "Your signature is placed on the letter only when you sign it yourself."))
        return self.get(letter.id)

    def recall(self, letter_id: int) -> OfficialLetter:
        """Back to draft for corrections - every signature collected so far is cleared."""
        letter = self.get(letter_id)
        self._require(letter, LetterStatus.AWAITING_SIGNATURES, "Only a letter awaiting signatures can be recalled")
        letter.status = LetterStatus.DRAFT
        letter.sent_at = None
        for s in letter.signatories:
            s.status, s.signed_at, s.signed_by, s.signed_ip = SignatoryStatus.PENDING, None, None, None
            s.signature_image_id, s.decline_reason, s.marked_by = None, None, None
        self.db.commit()
        return self.get(letter.id)

    def _my_slot(self, letter: OfficialLetter, user: User) -> LetterSignatory:
        slot = next((s for s in letter.signatories if s.member and s.member.user_id == user.id), None)
        if not slot:
            raise HTTPException(status_code=403, detail="You are not a signatory of this letter")
        return slot

    def sign(self, letter_id: int, user: User, password: str, ip: Optional[str]) -> Tuple[OfficialLetter, LetterSignatory]:
        letter = self.get(letter_id)
        slot = self._my_slot(letter, user)
        self._require(letter, LetterStatus.AWAITING_SIGNATURES, "This letter is not awaiting signatures")
        if slot.status != SignatoryStatus.PENDING:
            raise HTTPException(status_code=409, detail="You have already responded to this letter")
        if not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect password")
        image = self.current_image(LetterImageKind.SIGNATURE, slot.member_id)
        if not image:
            raise HTTPException(status_code=409, detail="No signature is on file for you yet - upload one first")
        slot.status, slot.signed_at, slot.signed_by = SignatoryStatus.SIGNED, datetime.utcnow(), user.id
        slot.signed_ip, slot.signature_image_id = (ip or "")[:64] or None, image.id
        self.db.commit()
        self._mail_member(slot.member, f"You signed: {letter.subject}", (
            f"Your signature was placed on a letter of {self._temple_name()} as {self._as(slot)}.\n\n"
            f"Subject: {letter.subject}\nSigned: {slot.signed_at:%d-%m-%Y %H:%M} UTC from {slot.signed_ip or 'unknown IP'}\n\n"
            "If this was not you, contact the temple office immediately and change your password."))
        return self.get(letter.id), slot

    def decline(self, letter_id: int, user: User, reason: str) -> Tuple[OfficialLetter, LetterSignatory]:
        letter = self.get(letter_id)
        slot = self._my_slot(letter, user)
        self._require(letter, LetterStatus.AWAITING_SIGNATURES, "This letter is not awaiting signatures")
        if slot.status != SignatoryStatus.PENDING:
            raise HTTPException(status_code=409, detail="You have already responded to this letter")
        slot.status, slot.decline_reason = SignatoryStatus.DECLINED, reason
        self.db.commit()
        return self.get(letter.id), slot

    def mark_paper(self, letter_id: int, signatory_id: int, user: User) -> Tuple[OfficialLetter, LetterSignatory]:
        """This signatory will sign the printed letter in ink - no stored signature is used."""
        letter = self.get(letter_id)
        self._require(letter, LetterStatus.AWAITING_SIGNATURES, "This letter is not awaiting signatures")
        slot = next((s for s in letter.signatories if s.id == signatory_id), None)
        if not slot:
            raise HTTPException(status_code=404, detail="Signatory not found")
        if slot.status not in (SignatoryStatus.PENDING, SignatoryStatus.DECLINED):
            raise HTTPException(status_code=409, detail="This signatory has already signed")
        slot.status, slot.marked_by, slot.decline_reason = SignatoryStatus.PAPER, user.id, None
        self.db.commit()
        return self.get(letter.id), slot

    def issue(self, letter_id: int, user: User) -> OfficialLetter:
        letter = self.get(letter_id)
        self._require(letter, LetterStatus.AWAITING_SIGNATURES, "Send the letter for signatures first")
        waiting = [s.name for s in letter.signatories if s.status not in _DONE]
        if waiting:
            raise HTTPException(status_code=409, detail=f"Still waiting on: {', '.join(waiting)}")
        seal_id = None
        if letter.include_seal:
            seal = self.current_image(LetterImageKind.SEAL)
            if not seal:
                raise HTTPException(status_code=409, detail="Upload the temple seal first, or untick 'include seal'")
            seal_id = seal.id
        now = datetime.utcnow()
        for attempt in range(5):
            letter.seal_image_id = seal_id
            letter.reference_number = self._next_reference(letter.letter_date.year, attempt)
            letter.status, letter.issued_at, letter.issued_by = LetterStatus.ISSUED, now, user.id
            try:
                self.db.commit()
                break
            except IntegrityError:  # two letters issued at the same moment - take the next number
                self.db.rollback()
                letter = self.get(letter_id)
        else:
            raise HTTPException(status_code=409, detail="Could not number the letter - please try again")
        return self.get(letter.id)

    def revoke(self, letter_id: int, user: User, reason: str) -> OfficialLetter:
        letter = self.get(letter_id)
        self._require(letter, LetterStatus.ISSUED, "Only an issued letter can be revoked")
        letter.status, letter.revoked_at, letter.revoked_by, letter.revoke_reason = (
            LetterStatus.REVOKED, datetime.utcnow(), user.id, reason)
        self.db.commit()
        return self.get(letter.id)

    def can_view(self, letter: OfficialLetter, user: User, can_read_all: bool) -> bool:
        return can_read_all or any(s.member and s.member.user_id == user.id for s in letter.signatories)

    # ---- my signatures ----------------------------------------------------------------------
    def my_member(self, user: User) -> Optional[Member]:
        return self.db.query(Member).filter(Member.user_id == user.id, Member.is_active.is_(True)).first()

    def mine(self, user: User) -> dict:
        member = self.my_member(user)
        if not member:
            return {"member_id": None}
        image = self.current_image(LetterImageKind.SIGNATURE, member.id)
        rows = (self.db.query(LetterSignatory, OfficialLetter)
                .join(OfficialLetter, OfficialLetter.id == LetterSignatory.letter_id)
                .options(joinedload(OfficialLetter.creator))
                .filter(LetterSignatory.member_id == member.id, LetterSignatory.status == SignatoryStatus.PENDING,
                        OfficialLetter.status == LetterStatus.AWAITING_SIGNATURES)
                .order_by(OfficialLetter.sent_at.desc()).all())
        return {
            "member_id": member.id, "member_name": member.name, "has_signature": image is not None,
            "uploaded_at": image.created_at if image else None,
            "pending": [{"letter_id": l.id, "signatory_id": s.id, "role": s.role, "subject": l.subject,
                         "kind": l.kind, "letter_date": l.letter_date, "recipient_name": l.recipient_name,
                         "sent_at": l.sent_at, "requested_by": l.creator.username if l.creator else None}
                        for s, l in rows],
        }

    # ---- signature & seal images ------------------------------------------------------------
    def current_image(self, kind: LetterImageKind, member_id: Optional[int] = None) -> Optional[LetterImage]:
        query = self.db.query(LetterImage).filter(LetterImage.kind == kind, LetterImage.retired_at.is_(None))
        if kind == LetterImageKind.SIGNATURE:
            query = query.filter(LetterImage.member_id == member_id)
        return query.order_by(LetterImage.id.desc()).first()

    def _current_signature_members(self, member_ids: set) -> set:
        if not member_ids:
            return set()
        rows = self.db.query(LetterImage.member_id).filter(
            LetterImage.kind == LetterImageKind.SIGNATURE, LetterImage.retired_at.is_(None),
            LetterImage.member_id.in_(member_ids)).distinct().all()
        return {r[0] for r in rows}

    def signature_statuses(self) -> List[dict]:
        members = (self.db.query(Member).options(joinedload(Member.user))
                   .order_by(Member.is_active.desc(), Member.sort_order, Member.name).all())
        latest = dict(self.db.query(LetterImage.member_id, func.max(LetterImage.created_at)).filter(
            LetterImage.kind == LetterImageKind.SIGNATURE, LetterImage.retired_at.is_(None)
        ).group_by(LetterImage.member_id).all())
        return [{"member_id": m.id, "name": m.name, "position": m.position, "is_active": m.is_active,
                 "has_login": m.user_id is not None, "linked_username": m.user.username if m.user else None,
                 "has_signature": m.id in latest, "uploaded_at": latest.get(m.id)} for m in members]

    def link_login(self, member: Member, user_id: Optional[int], actor: User) -> Tuple[Optional[str], Optional[str]]:
        """Link (or unlink) the login that signs letters as this member. Returns the
        (previous, new) usernames. Moving the link away from a login retires the stored
        signature, so whoever holds the new login can't sign with a signature that was
        put on file for someone else - a fresh one has to be uploaded (which emails the
        member again)."""
        if member.user_id == user_id:
            raise HTTPException(status_code=409, detail="Nothing to change")
        user = None
        if user_id is not None:
            user = self.db.get(User, user_id)
            if not user or not user.is_active:
                raise HTTPException(status_code=400, detail="Choose an active login")
            other = self.db.query(Member).filter(Member.user_id == user_id, Member.id != member.id).first()
            if other:
                raise HTTPException(status_code=409, detail=f"That login is already linked to {other.name}")
        previous = member.user.username if member.user else None
        if member.user_id is not None:
            self.retire_image(LetterImageKind.SIGNATURE, member.id, commit=False)
        member.user_id = user_id
        self.db.commit()
        self.db.refresh(member)
        if user:
            body = (f"{actor.username} linked the login '{user.username}' to the committee member record of "
                    f"{member.name} at {self._temple_name()}.\n\nThat login can now sign temple letters as "
                    f"{member.name}, at {settings.FRONTEND_BASE_URL}/sign-letters.\n\n"
                    "If this is wrong, contact the temple office immediately.")
            self._mail_member(member, "Your login was linked for signing temple letters", body)
            if user.email and user.email != member.email:
                self.email.send(user.email, "Your login was linked for signing temple letters", body)
        return previous, user.username if user else None

    def seal_status(self) -> dict:
        seal = self.current_image(LetterImageKind.SEAL)
        return {"has_seal": seal is not None, "uploaded_at": seal.created_at if seal else None}

    def get_member(self, member_id: int) -> Member:
        member = self.db.get(Member, member_id)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        return member

    def store_image(self, kind: LetterImageKind, image: str, user: User, member: Optional[Member] = None) -> LetterImage:
        raw = decode_data_url(image)
        if len(raw) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="That image is too large - use one under 6 MB")
        png, width, height, digest = clean_mark(raw, kind)
        self.retire_image(kind, member.id if member else None, commit=False)
        row = LetterImage(kind=kind, member_id=member.id if member else None, data=png, width=width, height=height,
                          sha256=digest, uploaded_by=user.id)
        self.db.add(row)
        self.db.commit()
        if member and kind == LetterImageKind.SIGNATURE and member.user_id != user.id:
            self._mail_member(member, "Your signature was added to the temple's letter system", (
                f"{user.username} uploaded your signature to {self._temple_name()}'s official letter system.\n\n"
                "It is placed on a letter only when you sign that letter yourself, from your own login, "
                f"at {settings.FRONTEND_BASE_URL}/sign-letters - nobody else can apply it.\n\n"
                "If you did not agree to this, contact the temple office."))
        return row

    def retire_image(self, kind: LetterImageKind, member_id: Optional[int], commit: bool = True) -> int:
        query = self.db.query(LetterImage).filter(LetterImage.kind == kind, LetterImage.retired_at.is_(None))
        if kind == LetterImageKind.SIGNATURE:
            query = query.filter(LetterImage.member_id == member_id)
        count = query.update({LetterImage.retired_at: datetime.utcnow()}, synchronize_session=False)
        if commit:
            self.db.commit()
        return count

    # ---- public verification ----------------------------------------------------------------
    def verification(self, token: str) -> dict:
        letter = self._query().filter(OfficialLetter.verify_token == token).first()
        if not letter or letter.status not in (LetterStatus.ISSUED, LetterStatus.REVOKED):
            raise HTTPException(status_code=404, detail="No issued letter matches this link")
        return {
            "reference_number": letter.reference_number, "status": letter.status, "kind_label": LABELS[letter.kind],
            "subject": letter.subject, "recipient_name": letter.recipient_name, "letter_date": letter.letter_date,
            "issued_at": letter.issued_at, "revoked_at": letter.revoked_at, "revoke_reason": letter.revoke_reason,
            "temple_name": self._temple_name(),
            "signatories": [{"name": s.name, "designation": s.designation, "role": s.role,
                             "method": "digital" if s.status == SignatoryStatus.SIGNED else "ink",
                             "signed_at": s.signed_at} for s in letter.signatories],
        }

    # ---- helpers ----------------------------------------------------------------------------
    def _temple(self) -> Optional[Temple]:
        return self.db.query(Temple).filter(Temple.is_active.is_(True)).first()

    def _temple_name(self) -> str:
        temple = self._temple()
        return temple.name if temple else "Sri Varasidhi Vinayaka Swamy Devasthanam"

    @staticmethod
    def _as(slot: LetterSignatory) -> str:
        return "attestor" if slot.role == SignatoryRole.ATTESTOR else "signatory"

    @staticmethod
    def _require(letter: OfficialLetter, status: LetterStatus, message: str) -> None:
        if letter.status != status:
            raise HTTPException(status_code=409, detail=message)

    def _next_reference(self, year: int, bump: int = 0) -> str:
        prefix = f"{REFERENCE_PREFIX}/{year}/"
        count = self.db.query(func.count(OfficialLetter.id)).filter(
            OfficialLetter.reference_number.like(f"{prefix}%")).scalar() or 0
        return f"{prefix}{count + 1 + bump:04d}"

    def _mail_member(self, member: Optional[Member], subject: str, body: str) -> None:
        if not member:
            return
        to = (member.user.email if member.user and member.user.email else None) or member.email
        if to:
            self.email.send(to, subject, f"Namaskaram {member.name},\n\n{body}")
