"""Official letters: drafting and issuing (letters:write), reading (letters:read),
signing by the signatories themselves (any signed-in user linked to a committee
member), signature & seal images, and the public verification page."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from app.core.pagination import PageParams, page_params, set_total
from app.core.rbac import Permission, has_permission
from app.models.letter import LetterImageKind, LetterStatus
from app.models.user import User
from app.repositories.temple_repo import TempleRepository
from app.schemas.letter import (
    ImageIn, LetterIn, LetterOut, LetterTemplate, LetterVerification, LoginLinkIn, MySignature, ReasonIn, SealStatus,
    SignIn,
    SignatureStatus,
)
from app.services.letter_pdf_service import generate_letter_pdf
from app.services.letter_service import LetterService
from app.utils.dependencies import AuditContext, get_audit, get_current_user, get_db, require_permission
from app.utils.rate_limiter import get_client_ip

router = APIRouter(prefix="/letters", tags=["letters"])

_read = require_permission(Permission.LETTERS_READ)
_write = require_permission(Permission.LETTERS_WRITE)
# Which login signs as which member is an identity decision: Super Admin only.
_link = require_permission(Permission.LETTERS_WRITE, Permission.USERS_MANAGE)
_NO_STORE = {"Cache-Control": "no-store, private"}


def get_letter_service(db: Session = Depends(get_db)) -> LetterService:
    return LetterService(db)


def _png(data: bytes) -> Response:
    return Response(content=data, media_type="image/png", headers=_NO_STORE)


# ---- public verification ------------------------------------------------------------------
@router.get("/verify/{token}", response_model=LetterVerification)
def verify(token: str, service: LetterService = Depends(get_letter_service)):
    """What a QR code on a printed letter opens: confirms the letter was issued by the
    temple (or shows that it was revoked). No login; the token is unguessable."""
    if not (10 <= len(token) <= 40):
        raise HTTPException(status_code=404, detail="No issued letter matches this link")
    return service.verification(token)


# ---- my signature & letters awaiting it ---------------------------------------------------
@router.get("/mine", response_model=MySignature)
def mine(service: LetterService = Depends(get_letter_service), user: User = Depends(get_current_user)):
    return service.mine(user)


def _my_member(service: LetterService, user: User):
    member = service.my_member(user)
    if not member:
        raise HTTPException(status_code=403, detail="Your login is not linked to a committee member")
    return member


@router.put("/mine/signature", response_model=MySignature)
def upload_my_signature(payload: ImageIn, service: LetterService = Depends(get_letter_service),
                        audit: AuditContext = Depends(get_audit), user: User = Depends(get_current_user)):
    member = _my_member(service, user)
    service.store_image(LetterImageKind.SIGNATURE, payload.image, user, member)
    audit.log("UPLOAD_SIGNATURE", "member", member.id, f"Uploaded own signature ({member.name})")
    return service.mine(user)


@router.get("/mine/signature.png")
def my_signature_png(service: LetterService = Depends(get_letter_service), user: User = Depends(get_current_user)):
    image = service.current_image(LetterImageKind.SIGNATURE, _my_member(service, user).id)
    if not image:
        raise HTTPException(status_code=404, detail="No signature on file")
    return _png(image.data)


# ---- signatures & seal (admin) ------------------------------------------------------------
@router.get("/signatures", response_model=List[SignatureStatus], dependencies=[Depends(_write)])
def signatures(service: LetterService = Depends(get_letter_service)):
    return service.signature_statuses()


@router.put("/signatures/{member_id}", response_model=SignatureStatus)
def upload_signature(member_id: int, payload: ImageIn, service: LetterService = Depends(get_letter_service),
                     audit: AuditContext = Depends(get_audit), user: User = Depends(_write)):
    member = service.get_member(member_id)
    service.store_image(LetterImageKind.SIGNATURE, payload.image, user, member)
    audit.log("UPLOAD_SIGNATURE", "member", member.id, f"Uploaded signature of {member.name}")
    return next(s for s in service.signature_statuses() if s["member_id"] == member.id)


@router.delete("/signatures/{member_id}", status_code=204)
def remove_signature(member_id: int, service: LetterService = Depends(get_letter_service),
                     audit: AuditContext = Depends(get_audit), _: User = Depends(_write)):
    member = service.get_member(member_id)
    if service.retire_image(LetterImageKind.SIGNATURE, member.id):
        audit.log("REMOVE_SIGNATURE", "member", member.id, f"Removed signature of {member.name}")
    return Response(status_code=204)


@router.put("/signatures/{member_id}/login", response_model=SignatureStatus)
def link_login(member_id: int, payload: LoginLinkIn, service: LetterService = Depends(get_letter_service),
               audit: AuditContext = Depends(get_audit), user: User = Depends(_link)):
    member = service.get_member(member_id)
    before, after = service.link_login(member, payload.user_id, user)
    summary = (f"Linked login '{after}' to member {member.name}" if after
               else f"Unlinked login '{before}' from member {member.name}")
    audit.log("LINK_LOGIN", "member", member.id, summary, {"from": before, "to": after})
    return next(s for s in service.signature_statuses() if s["member_id"] == member.id)


@router.get("/signatures/{member_id}.png", dependencies=[Depends(_write)])
def signature_png(member_id: int, service: LetterService = Depends(get_letter_service)):
    image = service.current_image(LetterImageKind.SIGNATURE, member_id)
    if not image:
        raise HTTPException(status_code=404, detail="No signature on file")
    return _png(image.data)


@router.get("/seal", response_model=SealStatus, dependencies=[Depends(_write)])
def seal(service: LetterService = Depends(get_letter_service)):
    return service.seal_status()


@router.put("/seal", response_model=SealStatus)
def upload_seal(payload: ImageIn, service: LetterService = Depends(get_letter_service),
                audit: AuditContext = Depends(get_audit), user: User = Depends(_write)):
    service.store_image(LetterImageKind.SEAL, payload.image, user)
    audit.log("UPLOAD_SEAL", "temple", None, "Uploaded the temple seal for official letters")
    return service.seal_status()


@router.delete("/seal", status_code=204)
def remove_seal(service: LetterService = Depends(get_letter_service), audit: AuditContext = Depends(get_audit),
                _: User = Depends(_write)):
    if service.retire_image(LetterImageKind.SEAL, None):
        audit.log("REMOVE_SEAL", "temple", None, "Removed the temple seal for official letters")
    return Response(status_code=204)


@router.get("/seal.png", dependencies=[Depends(_write)])
def seal_png(service: LetterService = Depends(get_letter_service)):
    image = service.current_image(LetterImageKind.SEAL)
    if not image:
        raise HTTPException(status_code=404, detail="No seal on file")
    return _png(image.data)


# ---- letters ------------------------------------------------------------------------------
@router.get("/templates", response_model=List[LetterTemplate], dependencies=[Depends(_write)])
def templates(service: LetterService = Depends(get_letter_service)):
    return service.templates()


@router.get("", response_model=List[LetterOut], dependencies=[Depends(_read)])
def list_letters(response: Response, status: Optional[LetterStatus] = None,
                 q: Optional[str] = Query(None, max_length=100), params: PageParams = Depends(page_params),
                 service: LetterService = Depends(get_letter_service)):
    rows, total = service.list(status, q, params)
    set_total(response, total)
    return [service.out(l) for l in rows]


@router.post("", response_model=LetterOut, status_code=201)
def create_letter(payload: LetterIn, service: LetterService = Depends(get_letter_service),
                  audit: AuditContext = Depends(get_audit), user: User = Depends(_write)):
    letter = service.create(payload, user)
    audit.log("CREATE", "letter", letter.id, f"Drafted letter '{letter.subject}'",
              {"kind": letter.kind, "signatories": [s.name for s in letter.signatories]})
    return service.out(letter)


@router.get("/{letter_id}", response_model=LetterOut)
def get_letter(letter_id: int, service: LetterService = Depends(get_letter_service),
               user: User = Depends(get_current_user)):
    letter = service.get(letter_id)
    if not service.can_view(letter, user, has_permission(user.roles, Permission.LETTERS_READ)):
        raise HTTPException(status_code=403, detail="You do not have permission to do this")
    return service.out(letter)


@router.put("/{letter_id}", response_model=LetterOut)
def update_letter(letter_id: int, payload: LetterIn, service: LetterService = Depends(get_letter_service),
                  audit: AuditContext = Depends(get_audit), _: User = Depends(_write)):
    letter = service.update(letter_id, payload)
    audit.log("UPDATE", "letter", letter.id, f"Edited draft letter '{letter.subject}'")
    return service.out(letter)


@router.delete("/{letter_id}", status_code=204)
def delete_letter(letter_id: int, service: LetterService = Depends(get_letter_service),
                  audit: AuditContext = Depends(get_audit), _: User = Depends(_write)):
    letter = service.delete(letter_id)
    audit.log("DELETE", "letter", letter_id, f"Deleted draft letter '{letter.subject}'")
    return Response(status_code=204)


@router.post("/{letter_id}/send", response_model=LetterOut)
def send_letter(letter_id: int, service: LetterService = Depends(get_letter_service),
                audit: AuditContext = Depends(get_audit), _: User = Depends(_write)):
    letter = service.send(letter_id)
    audit.log("SEND", "letter", letter.id, f"Sent '{letter.subject}' for signatures")
    return service.out(letter)


@router.post("/{letter_id}/recall", response_model=LetterOut)
def recall_letter(letter_id: int, service: LetterService = Depends(get_letter_service),
                  audit: AuditContext = Depends(get_audit), _: User = Depends(_write)):
    letter = service.recall(letter_id)
    audit.log("RECALL", "letter", letter.id, f"Recalled '{letter.subject}' to draft (signatures cleared)")
    return service.out(letter)


@router.post("/{letter_id}/signatories/{signatory_id}/paper", response_model=LetterOut)
def mark_paper(letter_id: int, signatory_id: int, service: LetterService = Depends(get_letter_service),
               audit: AuditContext = Depends(get_audit), user: User = Depends(_write)):
    letter, slot = service.mark_paper(letter_id, signatory_id, user)
    audit.log("MARK_PAPER", "letter", letter.id, f"{slot.name} will sign '{letter.subject}' in ink")
    return service.out(letter)


@router.post("/{letter_id}/issue", response_model=LetterOut)
def issue_letter(letter_id: int, service: LetterService = Depends(get_letter_service),
                 audit: AuditContext = Depends(get_audit), user: User = Depends(_write)):
    letter = service.issue(letter_id, user)
    audit.log("ISSUE", "letter", letter.id, f"Issued {letter.reference_number}: '{letter.subject}'")
    return service.out(letter)


@router.post("/{letter_id}/revoke", response_model=LetterOut)
def revoke_letter(letter_id: int, payload: ReasonIn, service: LetterService = Depends(get_letter_service),
                  audit: AuditContext = Depends(get_audit), user: User = Depends(_write)):
    letter = service.revoke(letter_id, user, payload.reason)
    audit.log("REVOKE", "letter", letter.id, f"Revoked {letter.reference_number}: {payload.reason}")
    return service.out(letter)


@router.post("/{letter_id}/sign", response_model=LetterOut)
def sign_letter(letter_id: int, payload: SignIn, request: Request,
                service: LetterService = Depends(get_letter_service), audit: AuditContext = Depends(get_audit),
                user: User = Depends(get_current_user)):
    try:
        letter, slot = service.sign(letter_id, user, payload.password, get_client_ip(request))
    except HTTPException as exc:
        if exc.detail == "Incorrect password":
            audit.log("SIGN_FAILED", "letter", letter_id, "Wrong password while signing a letter")
        raise
    audit.log("SIGN", "letter", letter.id, f"{slot.name} signed '{letter.subject}'")
    return service.out(letter)


@router.post("/{letter_id}/decline", response_model=LetterOut)
def decline_letter(letter_id: int, payload: ReasonIn, service: LetterService = Depends(get_letter_service),
                   audit: AuditContext = Depends(get_audit), user: User = Depends(get_current_user)):
    letter, slot = service.decline(letter_id, user, payload.reason)
    audit.log("DECLINE", "letter", letter.id, f"{slot.name} declined to sign '{letter.subject}'",
              {"reason": payload.reason})
    return service.out(letter)


@router.get("/{letter_id}/pdf")
def letter_pdf(letter_id: int, db: Session = Depends(get_db), service: LetterService = Depends(get_letter_service),
               user: User = Depends(get_current_user)):
    letter = service.get(letter_id)
    if not service.can_view(letter, user, has_permission(user.roles, Permission.LETTERS_READ)):
        raise HTTPException(status_code=403, detail="You do not have permission to do this")
    pdf = generate_letter_pdf(letter, TempleRepository(db).get_active())
    name = (letter.reference_number or f"draft-{letter.id}").replace("/", "-")
    return Response(content=pdf, media_type="application/pdf",
                    headers={**_NO_STORE, "Content-Disposition": f'inline; filename="{name}.pdf"'})
