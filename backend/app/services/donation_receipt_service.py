"""Donation receipt PDF - system generated, so it carries no signature line:
the receipt number (unique, issued once) and the temple's records are what
make it valid, and the footer says so."""
from datetime import datetime
from functools import lru_cache
from decimal import ROUND_HALF_UP, Decimal
from io import BytesIO
from pathlib import Path
from typing import List, Optional
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.donation import Donation
from app.models.temple import Temple

LOGO_PATH = Path(__file__).resolve().parents[2] / "assets" / "logo.png"
IST = ZoneInfo("Asia/Kolkata")

MAROON = colors.HexColor("#7a1c1c")
SAFFRON = colors.HexColor("#d97a1f")
CREAM = colors.HexColor("#fbf6ec")
RULE = colors.HexColor("#e7c9a0")
MUTED = colors.HexColor("#6b6b6b")

PAYMENT_MODES = {"CASH": "Cash", "UPI": "UPI", "BANK": "Bank transfer", "CHEQUE": "Cheque"}


def _safe(text: Optional[str], fallback: str = "-") -> str:
    """Escape user-provided text: reportlab Paragraphs interpret <tags>."""
    return escape(text.strip()) if text and text.strip() else fallback


# ------------------------------------------------------------ amount in words
_ONES = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
         "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
_TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]


def _below_hundred(n: int) -> str:
    return _ONES[n] if n < 20 else " ".join(w for w in (_TENS[n // 10], _ONES[n % 10]) if w)


def _below_thousand(n: int) -> str:
    hundreds, rest = divmod(n, 100)
    words = [f"{_ONES[hundreds]} Hundred"] if hundreds else []
    if rest:
        words.append(_below_hundred(rest))
    return " ".join(words)


def _indian_words(n: int) -> str:
    """Whole number in words, Indian grouping: 12,34,567 -> Twelve Lakh Thirty
    Four Thousand Five Hundred Sixty Seven."""
    if n == 0:
        return "Zero"
    parts = []
    crore, n = divmod(n, 10_000_000)
    lakh, n = divmod(n, 100_000)
    thousand, n = divmod(n, 1_000)
    if crore:
        parts.append(f"{_indian_words(crore)} Crore")
    if lakh:
        parts.append(f"{_below_hundred(lakh)} Lakh")
    if thousand:
        parts.append(f"{_below_hundred(thousand)} Thousand")
    if n:
        parts.append(_below_thousand(n))
    return " ".join(parts)


def amount_in_words(amount) -> str:
    """Rupees 1,250.50 -> "Rupees One Thousand Two Hundred Fifty and Fifty Paise Only"."""
    value = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    rupees, paise = divmod(int(value * 100), 100)
    words = f"Rupees {_indian_words(rupees)}"
    if paise:
        words += f" and {_below_hundred(paise)} Paise"
    return f"{words} Only"


def _money(amount) -> str:
    """Indian digit grouping: 123456.5 -> 1,23,456.50"""
    value = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    whole, frac = f"{value:.2f}".split(".")
    sign = "-" if whole.startswith("-") else ""
    whole = whole.lstrip("-")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        whole = ",".join(groups + [tail])
    return f"{sign}{whole}.{frac}"


# --------------------------------------------------------------------- styles
def _style(name: str, **kw) -> ParagraphStyle:
    base = dict(fontName="Helvetica", fontSize=9.5, leading=13, textColor=colors.black)
    base.update(kw)
    return ParagraphStyle(name, **base)


S = {
    "temple": _style("temple", fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=MAROON),
    "tagline": _style("tagline", fontName="Helvetica-Oblique", fontSize=9, textColor=SAFFRON),
    "contact": _style("contact", fontSize=8.5, leading=11.5, textColor=MUTED),
    "title": _style("title", fontName="Helvetica-Bold", fontSize=14, leading=18, alignment=TA_CENTER,
                    textColor=MAROON),
    "subtitle": _style("subtitle", fontSize=8, alignment=TA_CENTER, textColor=MUTED),
    "section": _style("section", fontName="Helvetica-Bold", fontSize=9, textColor=MAROON),
    "label": _style("label", fontName="Helvetica-Bold", fontSize=9, textColor=MUTED),
    "value": _style("value"),
    "amount": _style("amount", fontName="Helvetica-Bold", fontSize=18, leading=22, alignment=TA_LEFT,
                     textColor=MAROON),
    "words": _style("words", fontName="Helvetica-Oblique", fontSize=9.5),
    "thanks": _style("thanks", fontSize=9.5, alignment=TA_CENTER, textColor=MAROON),
    "note": _style("note", fontName="Helvetica-Bold", fontSize=9, alignment=TA_CENTER),
    "fine": _style("fine", fontSize=7.5, leading=10, alignment=TA_CENTER, textColor=MUTED),
}


@lru_cache(maxsize=1)
def _logo_bytes() -> bytes:
    """The logo downscaled for print (~300 dpi at 24 mm) - the 512 px original
    would triple the PDF's size for no visible gain."""
    with PILImage.open(LOGO_PATH) as img:
        img = img.convert("RGBA")
        img.thumbnail((280, 280))
        out = BytesIO()
        img.save(out, format="PNG", optimize=True)
        return out.getvalue()


def _logo_png() -> BytesIO:
    return BytesIO(_logo_bytes())


def _header(temple: Optional[Temple]) -> Table:
    name = temple.name if temple else "Sri Varasidhi Vinayaka Swamy Devasthanam"
    lines: List = [Paragraph(_safe(name), S["temple"])]
    if temple and temple.tagline:
        lines.append(Paragraph(_safe(temple.tagline), S["tagline"]))
    if temple:
        address = ", ".join(p for p in (temple.address, temple.village, temple.district, temple.state) if p)
        if temple.pincode:
            address = f"{address} - {temple.pincode}" if address else temple.pincode
        contact = " | ".join(p for p in (
            f"Phone: {temple.contact_phone}" if temple.contact_phone else "",
            f"Email: {temple.contact_email}" if temple.contact_email else "",
        ) if p)
        for line in (address, contact):
            if line:
                lines.append(Paragraph(_safe(line), S["contact"]))
    lines.append(Paragraph("svvdthorur.org", S["contact"]))

    logo = Image(_logo_png(), width=24 * mm, height=24 * mm) if LOGO_PATH.exists() else ""
    table = Table([[logo, lines]], colWidths=[28 * mm, None])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, SAFFRON),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


def _details(rows: List[tuple[str, str]], heading: str) -> Table:
    data = [[Paragraph(heading, S["section"]), ""]]
    data += [[Paragraph(label, S["label"]), Paragraph(value, S["value"])] for label, value in rows]
    table = Table(data, colWidths=[38 * mm, None])
    table.setStyle(TableStyle([
        ("SPAN", (0, 0), (-1, 0)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.75, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return table


class DonationReceiptService:
    @staticmethod
    def generate_receipt_pdf(donation: Donation, temple: Optional[Temple] = None,
                             generated_at: Optional[datetime] = None) -> bytes:
        """Render the A4 receipt for an issued donation receipt."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                                topMargin=16 * mm, bottomMargin=16 * mm,
                                title=f"Donation Receipt {donation.receipt_number or ''}".strip(),
                                author=temple.name if temple else "SVVD Thorur")
        donor = donation.donor
        issued = donation.receipt_generated_at or datetime.now()
        generated = (generated_at or datetime.now(IST)).astimezone(IST)

        elements: List = [_header(temple), Spacer(1, 10)]
        elements.append(Paragraph("DONATION RECEIPT", S["title"]))
        elements.append(Paragraph("Computer-generated receipt", S["subtitle"]))
        elements.append(Spacer(1, 10))

        # Receipt number / dates band
        band = Table([[
            Paragraph(f"<b>Receipt No.</b><br/>{_safe(donation.receipt_number, 'N/A')}", S["value"]),
            Paragraph(f"<b>Receipt Date</b><br/>{issued:%d-%m-%Y}", S["value"]),
            Paragraph(f"<b>Donation Date</b><br/>{donation.donated_on:%d-%m-%Y}", S["value"]),
        ]], colWidths=["34%", "33%", "33%"])
        band.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), CREAM),
            ("BOX", (0, 0), (-1, -1), 0.75, RULE),
            ("LINEAFTER", (0, 0), (1, 0), 0.75, RULE),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements += [band, Spacer(1, 12)]

        donor_rows = [("Received from", f"<b>{_safe(donor.name)}</b>")]
        for label, value in (("Phone", donor.phone), ("Email", donor.email), ("Address", donor.address),
                             ("PAN", donor.pan_number)):
            if value and value.strip():
                donor_rows.append((label, _safe(value).replace("\n", "<br/>")))
        elements += [_details(donor_rows, "DONOR DETAILS"), Spacer(1, 10)]

        mode = donation.payment_mode.value if hasattr(donation.payment_mode, "value") else str(donation.payment_mode)
        gift_rows = [("Donation type", _safe((donation.donation_type or "general").replace("_", " ").title()))]
        if donation.purpose and donation.purpose.strip():
            gift_rows.append(("Purpose", _safe(donation.purpose).replace("\n", "<br/>")))
        if donation.occasion and donation.occasion.strip():
            gift_rows.append(("Occasion", _safe(donation.occasion)))
        gift_rows.append(("Payment mode", PAYMENT_MODES.get(mode, _safe(mode))))
        if donation.recorded_by is not None:
            gift_rows.append(("Received by", _safe(donation.recorded_by.username)))
        elements += [_details(gift_rows, "DONATION DETAILS"), Spacer(1, 12)]

        amount = Table([
            [Paragraph("Amount received", S["label"]), Paragraph(f"Rs. {_money(donation.amount)}", S["amount"])],
            [Paragraph("In words", S["label"]), Paragraph(amount_in_words(donation.amount), S["words"])],
        ], colWidths=[38 * mm, None])
        amount.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, MAROON),
            ("BACKGROUND", (0, 0), (-1, -1), CREAM),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements += [amount, Spacer(1, 16)]

        elements.append(Paragraph(
            "Thank you for your generous contribution. May Sri Varasidhi Vinayaka Swamy bless you "
            "and your family.", S["thanks"]))
        elements.append(Spacer(1, 18))
        note = Table([[Paragraph(
            "This is a computer-generated receipt and does not require a signature.", S["note"])]])
        note.setStyle(TableStyle([
            ("LINEABOVE", (0, 0), (-1, 0), 0.75, RULE),
            ("LINEBELOW", (0, 0), (-1, 0), 0.75, RULE),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(note)
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(
            f"Generated on {generated:%d-%m-%Y %I:%M %p} IST. Receipt numbers are issued once per donation "
            "and recorded in the temple's accounts; please quote it in any correspondence. "
            "Privacy policy: svvdthorur.org/legal/privacy-policy",
            S["fine"]))

        doc.build(elements)
        return buffer.getvalue()
