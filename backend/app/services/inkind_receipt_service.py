"""Acknowledgement for a donation in kind (rice, oil, a silver lamp...).
Same look as the money receipt (donation_receipt_service), but it
acknowledges goods: what and how much, never a certified money value."""
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from typing import List, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.inventory import InventoryItem, StockMovement
from app.models.temple import Temple
from app.services.donation_receipt_service import (
    CREAM, IST, MAROON, RULE, S, _details, _header, _money, _safe,
)
from app.services.inventory_service import _fmt_qty


def generate_inkind_receipt_pdf(movement: StockMovement, item: InventoryItem, temple: Optional[Temple],
                                received_by: Optional[str] = None,
                                generated_at: Optional[datetime] = None) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm,
                            title=f"Acknowledgement {movement.receipt_number or ''}".strip(),
                            author=temple.name if temple else "SVVD Thorur")
    generated = (generated_at or datetime.now(IST)).astimezone(IST)

    elements: List = [_header(temple), Spacer(1, 10)]
    elements.append(Paragraph("ACKNOWLEDGEMENT OF DONATION IN KIND", S["title"]))
    elements.append(Paragraph("Computer-generated acknowledgement", S["subtitle"]))
    elements.append(Spacer(1, 10))

    band = Table([[
        Paragraph(f"<b>Receipt No.</b><br/>{_safe(movement.receipt_number, 'N/A')}", S["value"]),
        Paragraph(f"<b>Date received</b><br/>{movement.movement_date:%d-%m-%Y}", S["value"]),
    ]], colWidths=["50%", "50%"])
    band.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CREAM),
        ("BOX", (0, 0), (-1, -1), 0.75, RULE),
        ("LINEAFTER", (0, 0), (0, 0), 0.75, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements += [band, Spacer(1, 12)]

    donor_rows = [("Received from", f"<b>{_safe(movement.donor_name)}</b>")]
    for label, value in (("Phone", movement.donor_phone), ("Address", movement.donor_address)):
        if value and value.strip():
            donor_rows.append((label, _safe(value)))
    elements += [_details(donor_rows, "DONOR DETAILS"), Spacer(1, 10)]

    goods = Table([
        [Paragraph("Item", S["label"]), Paragraph(f"<b>{_safe(item.name)}</b>", S["amount"])],
        [Paragraph("Quantity", S["label"]), Paragraph(f"{_fmt_qty(Decimal(movement.quantity))} {_safe(item.unit)}",
                                                      S["value"])],
    ], colWidths=[38 * mm, None])
    goods.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, MAROON),
        ("BACKGROUND", (0, 0), (-1, -1), CREAM),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements += [goods, Spacer(1, 10)]

    extra = []
    if item.material:
        extra.append(("Material", _safe(item.material.title())))
    if movement.notes:
        extra.append(("Notes", _safe(movement.notes)))
    if movement.total_value:
        extra.append(("Estimated value", f"Rs. {_money(movement.total_value)} (temple's estimate, for its records)"))
    if received_by:
        extra.append(("Received by", _safe(received_by)))
    if extra:
        elements += [_details(extra, "DETAILS"), Spacer(1, 12)]

    elements.append(Paragraph(
        "Thank you for your offering. May Sri Varasidhi Vinayaka Swamy bless you and your family.", S["thanks"]))
    elements.append(Spacer(1, 18))
    note = Table([[Paragraph(
        "This is a computer-generated acknowledgement and does not require a signature.", S["note"])]])
    note.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.75, RULE),
        ("LINEBELOW", (0, 0), (-1, 0), 0.75, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements += [note, Spacer(1, 6)]
    elements.append(Paragraph(
        f"Generated on {generated:%d-%m-%Y %I:%M %p} IST. This acknowledges goods received by the temple; "
        "it is not a receipt for money. Privacy policy: svvdthorur.org/legal/privacy-policy", S["fine"]))
    doc.build(elements)
    return buffer.getvalue()
