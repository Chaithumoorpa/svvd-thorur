from datetime import datetime
from io import BytesIO
from typing import Optional
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A5, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.donation import Donation
from app.models.temple import Temple


def _safe(text: Optional[str], fallback: str = "-") -> str:
    """Escape user-provided text: reportlab Paragraphs interpret <tags>."""
    return escape(text.strip()) if text and text.strip() else fallback


def _temple_lines(temple: Optional[Temple]) -> tuple[str, str]:
    if not temple:
        return "Temple", ""
    parts = [temple.address, temple.village, temple.district, temple.state, temple.pincode]
    return temple.name, ", ".join(p for p in parts if p)


class DonationReceiptService:
    @staticmethod
    def generate_receipt_pdf(donation: Donation, temple: Optional[Temple] = None) -> bytes:
        """Render an A5-landscape receipt for an issued donation receipt."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A5),
                                rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        styles = getSampleStyleSheet()
        elements = []

        temple_name, temple_address = _temple_lines(temple)
        elements.append(Paragraph(
            _safe(temple_name),
            ParagraphStyle("Header", parent=styles["Title"], fontSize=20, spaceAfter=6, textColor=colors.darkred),
        ))
        if temple_address:
            elements.append(Paragraph(
                _safe(temple_address),
                ParagraphStyle("Sub", parent=styles["Normal"], fontSize=10, alignment=1, spaceAfter=12),
            ))
        elements.append(Paragraph("Official Donation Receipt", styles["Heading3"]))
        elements.append(Spacer(1, 10))

        donor = donation.donor
        received = donation.receipt_generated_at or datetime.now()
        rows = [
            ["Receipt No:", donation.receipt_number or "N/A", "Date:", received.strftime("%d-%m-%Y")],
            ["Donor Name:", Paragraph(_safe(donor.name), styles["Normal"]), "", ""],
            ["Donated For:", Paragraph(_safe(donation.donation_type.title()), styles["Normal"]),
             "Payment Mode:", donation.payment_mode.value],
            ["Phone:", donor.phone or "N/A", "", ""],
        ]
        if donor.pan_number:
            rows.append(["PAN:", donor.pan_number, "", ""])
        table = Table(rows, colWidths=[1.2 * inch, 2.5 * inch, 1.1 * inch, 1.4 * inch])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

        elements.append(Paragraph(
            f"Amount Received: Rs. {donation.amount:,.2f}",
            ParagraphStyle("Amount", parent=styles["Heading2"], fontSize=16, alignment=1,
                           borderWidth=1, borderColor=colors.black, borderPadding=8),
        ))
        elements.append(Spacer(1, 28))

        signature = Table([["", "Authorized Signature"]], colWidths=[3.6 * inch, 2.6 * inch])
        signature.setStyle(TableStyle([
            ("ALIGN", (1, 0), (1, 0), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 18),
            ("LINEABOVE", (1, 0), (1, 0), 1, colors.black),
        ]))
        elements.append(signature)
        elements.append(Spacer(1, 14))
        elements.append(Paragraph(
            "This is a system-generated receipt.",
            ParagraphStyle("Sys", parent=styles["Normal"], fontSize=7, alignment=1, textColor=colors.grey),
        ))

        doc.build(elements)
        return buffer.getvalue()
