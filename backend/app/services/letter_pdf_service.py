"""Official letter / certificate PDF on the temple letterhead.

Issued letters carry their reference number, the temple seal, each signer's
signature (or a blank line for one signing in ink) and a QR code that opens
the public verification page. Anything not yet issued prints with a large
DRAFT watermark and no QR, so a preview can't pass for a real letter; a
revoked letter prints REVOKED.
"""
from datetime import datetime, timezone
from io import BytesIO
from typing import List, Optional

import qrcode
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.letter import LetterStatus, OfficialLetter, SignatoryRole, SignatoryStatus
from app.models.temple import Temple
from app.services.donation_receipt_service import IST, MAROON, MUTED, RULE, _header, _safe, _style
from app.services.letter_service import verify_url
from app.services.letter_templates import ATTESTOR_HEADINGS, CERTIFICATE_TITLES

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm
FOOTER_H = 30 * mm
SIG_H = 15 * mm
SEAL_MAX = 30 * mm
WIDE_SEAL_RATIO = 1.6          # wider than this (width / height) = a rectangular stamp
WIDE_SEAL_W, WIDE_SEAL_H = 56 * mm, 24 * mm

S = {
    "meta": _style("lmeta", fontSize=10, leading=13),
    "meta_r": _style("lmeta_r", fontSize=10, leading=13, alignment=TA_RIGHT),
    "trust": _style("ltrust", fontSize=8, leading=10, alignment=TA_CENTER, textColor=MUTED),
    "to": _style("lto", fontSize=10.5, leading=14),
    "subject": _style("lsubject", fontName="Helvetica-Bold", fontSize=10.5, leading=14),
    "cert": _style("lcert", fontName="Helvetica-Bold", fontSize=16, leading=20, alignment=TA_CENTER,
                   textColor=MAROON),
    "body": _style("lbody", fontSize=10.5, leading=15.5, alignment=TA_JUSTIFY),
    "closing": _style("lclosing", fontSize=10.5, leading=14),
    "for": _style("lfor", fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=MAROON),
    "sig_name": _style("lsig_name", fontName="Helvetica-Bold", fontSize=9.5, leading=12, alignment=TA_CENTER),
    "sig_role": _style("lsig_role", fontSize=8.5, leading=11, alignment=TA_CENTER),
    "sig_note": _style("lsig_note", fontSize=7, leading=9, alignment=TA_CENTER, textColor=MUTED),
    "attested": _style("lattested", fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=MAROON),
}


def _ist(utc_naive: datetime) -> datetime:
    return utc_naive.replace(tzinfo=timezone.utc).astimezone(IST)


def _image(png: bytes, max_w: float, max_h: float) -> Image:
    img = Image(BytesIO(png))
    scale = min(max_w / img.imageWidth, max_h / img.imageHeight)
    img.drawWidth, img.drawHeight = img.imageWidth * scale, img.imageHeight * scale
    return img


def _paragraphs(text: str, style) -> List:
    out: List = []
    for block in text.replace("\r\n", "\n").split("\n\n"):
        if block.strip():
            out += [Paragraph(_safe(block).replace("\n", "<br/>"), style), Spacer(1, 7)]
    return out


def _signature_cell(slot, width: float, issued: bool) -> List:
    signed_on = f"Digitally signed on {_ist(slot.signed_at):%d-%m-%Y}" if slot.signed_at else "Digitally signed"
    if slot.status == SignatoryStatus.SIGNED and slot.signature_image is not None and issued:
        mark, note = _image(slot.signature_image.data, width - 6 * mm, SIG_H), signed_on
    elif slot.status == SignatoryStatus.SIGNED:
        # A draft never carries the signature image itself - only issued letters do.
        mark, note = Spacer(1, SIG_H), f"{signed_on} (shown when issued)"
    else:
        mark = Spacer(1, SIG_H)
        note = {SignatoryStatus.PAPER: "", SignatoryStatus.DECLINED: "Declined"}.get(
            slot.status, "" if issued else "Awaiting signature")
    line = Table([[""]], colWidths=[width - 8 * mm], rowHeights=[1])
    line.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, -1), 0.6, colors.black)]))
    cell: List = [mark, line, Paragraph(_safe(slot.name), S["sig_name"])]
    if slot.designation:
        cell.append(Paragraph(_safe(slot.designation), S["sig_role"]))
    if note:
        cell.append(Paragraph(note, S["sig_note"]))
    return cell


def _seal(png: bytes) -> Image:
    """A round/square seal prints about 30 mm across, the size of a real one. A long
    rectangular rubber stamp (name and address lines) prints at its real width - about
    55 mm - so its text stays readable."""
    img = Image(BytesIO(png))
    if img.imageWidth >= img.imageHeight * WIDE_SEAL_RATIO:
        return _image(png, WIDE_SEAL_W, WIDE_SEAL_H)
    return _image(png, SEAL_MAX, SEAL_MAX)


def _signature_rows(slots, width: float, issued: bool, seal: Optional[Image]) -> Table:
    """Up to three signers per row; the seal, when there is one, sits in the first row's
    left cell - a column wide enough for it - with two signers beside it."""
    per_row = 3 if seal is None else 2
    seal_col = 0 if seal is None else max(width / 3, seal.drawWidth + 4 * mm)
    signer_w = (width - seal_col) / per_row
    rows, first = [], True
    for start in range(0, len(slots), per_row):
        chunk = slots[start:start + per_row]
        cells = [_signature_cell(s, signer_w, issued) for s in chunk]
        cells += [""] * (per_row - len(chunk))
        if seal is not None:
            cells = ([seal] if first else [""]) + cells
        rows.append(cells)
        first = False
    table = Table(rows, colWidths=([seal_col] if seal is not None else []) + [signer_w] * per_row)
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        *([("VALIGN", (0, 0), (0, 0), "MIDDLE")] if seal is not None else []),
    ]))
    return table


def _qr_png(url: str) -> bytes:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=6, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    out = BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(out, format="PNG")
    return out.getvalue()


def generate_letter_pdf(letter: OfficialLetter, temple: Optional[Temple],
                        generated_at: Optional[datetime] = None) -> bytes:
    buffer = BytesIO()
    issued = letter.status in (LetterStatus.ISSUED, LetterStatus.REVOKED)
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=14 * mm,
                            bottomMargin=FOOTER_H + 6 * mm,
                            title=f"{letter.reference_number or 'Draft'} - {letter.subject}",
                            author=temple.name if temple else "SVVD Thorur")
    width = PAGE_W - 2 * MARGIN
    temple_name = temple.name if temple else "Sri Varasidhi Vinayaka Swamy Devasthanam"

    elements: List = [_header(temple)]
    if temple:
        trust = " | ".join(p for p in (
            f"Regd. No. {temple.registration_number}" if temple.registration_number else "",
            f"PAN {temple.pan_number}" if temple.pan_number else "",
            f"80G {temple.eighty_g_number}" if temple.eighty_g_number else "",
        ) if p)
        if trust:
            elements += [Spacer(1, 3), Paragraph(_safe(trust), S["trust"])]
    elements.append(Spacer(1, 10))

    ref = _safe(letter.reference_number) if letter.reference_number else "<i>assigned when issued</i>"
    meta = Table([[Paragraph(f"<b>Ref:</b> {ref}", S["meta"]),
                   Paragraph(f"<b>Date:</b> {letter.letter_date:%d-%m-%Y}", S["meta_r"])]],
                 colWidths=[width * 0.6, width * 0.4])
    meta.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    elements += [meta, Spacer(1, 12)]

    title = CERTIFICATE_TITLES.get(letter.kind)
    if title:
        elements += [Paragraph(title, S["cert"]), Spacer(1, 4)]
        rule = Table([[""]], colWidths=[50 * mm], rowHeights=[1])
        rule.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, -1), 1, RULE)]))
        elements += [rule, Spacer(1, 14)]
    else:
        if letter.recipient_name or letter.recipient_address:
            lines = ["To,"] + ([_safe(letter.recipient_name)] if letter.recipient_name else [])
            if letter.recipient_address:
                lines += [_safe(l) for l in letter.recipient_address.splitlines() if l.strip()]
            elements += [Paragraph("<br/>".join(lines), S["to"]), Spacer(1, 10)]
        elements += [Paragraph(f"Subject: {_safe(letter.subject)}", S["subject"]), Spacer(1, 10)]
        if letter.salutation:
            elements += [Paragraph(_safe(letter.salutation), S["to"]), Spacer(1, 8)]

    elements += _paragraphs(letter.body, S["body"])

    closing: List = [Spacer(1, 6)]
    if letter.closing:
        closing.append(Paragraph(_safe(letter.closing), S["closing"]))
    closing += [Paragraph(f"For {_safe(temple_name)}", S["for"]), Spacer(1, 4)]

    seal = None
    if issued and letter.seal_image is not None:
        seal = _seal(letter.seal_image.data)
    signers = [s for s in letter.signatories if s.role == SignatoryRole.SIGNATORY]
    attestors = [s for s in letter.signatories if s.role == SignatoryRole.ATTESTOR]
    if signers:
        closing.append(_signature_rows(signers, width, issued, seal))
        seal = None
    elements.append(KeepTogether(closing))
    if attestors:
        elements.append(KeepTogether([Spacer(1, 4), Paragraph(ATTESTOR_HEADINGS.get(letter.kind, "ATTESTED BY"), S["attested"]), Spacer(1, 2),
                                      _signature_rows(attestors, width, issued, seal)]))

    generated = (generated_at or datetime.now(IST)).astimezone(IST)
    qr = _qr_png(verify_url(letter)) if issued else None
    watermark = {LetterStatus.REVOKED: "REVOKED"}.get(letter.status, None if issued else "DRAFT")

    def decorate(canvas, doc_):
        canvas.saveState()
        if watermark:
            canvas.setFont("Helvetica-Bold", 96)
            canvas.setFillColor(colors.Color(0.75, 0.1, 0.1, alpha=0.12) if watermark == "REVOKED"
                                else colors.Color(0.4, 0.4, 0.4, alpha=0.12))
            canvas.translate(PAGE_W / 2, PAGE_H / 2)
            canvas.rotate(40)
            canvas.drawCentredString(0, -30, watermark)
            canvas.rotate(-40)
            canvas.translate(-PAGE_W / 2, -PAGE_H / 2)
        y0 = 12 * mm
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.75)
        canvas.line(MARGIN, y0 + 22 * mm, PAGE_W - MARGIN, y0 + 22 * mm)
        canvas.setFillColor(MUTED)
        text_x = MARGIN
        if qr:
            canvas.drawImage(_qr_reader(qr), MARGIN, y0, width=20 * mm, height=20 * mm)
            text_x = MARGIN + 24 * mm
            canvas.setFont("Helvetica-Bold", 8)
            canvas.drawString(text_x, y0 + 15 * mm, f"Ref. {letter.reference_number}  -  issued "
                                                    f"{_ist(letter.issued_at):%d-%m-%Y}")
            canvas.setFont("Helvetica", 7.5)
            canvas.drawString(text_x, y0 + 10.5 * mm, "Verify this letter: scan the QR code or open")
            canvas.drawString(text_x, y0 + 6.5 * mm, verify_url(letter))
        else:
            canvas.setFont("Helvetica-Bold", 8)
            canvas.drawString(text_x, y0 + 12 * mm, "DRAFT - not valid. A letter is valid only once issued with a "
                                                    "reference number and verification QR code.")
        canvas.setFont("Helvetica", 7)
        canvas.drawString(text_x, y0 + 2 * mm, f"Generated {generated:%d-%m-%Y %I:%M %p} IST")
        canvas.drawRightString(PAGE_W - MARGIN, y0 + 2 * mm, f"Page {doc_.page}")
        canvas.restoreState()

    doc.build(elements, onFirstPage=decorate, onLaterPages=decorate)
    return buffer.getvalue()


def _qr_reader(png: bytes):
    from reportlab.lib.utils import ImageReader
    return ImageReader(BytesIO(png))
