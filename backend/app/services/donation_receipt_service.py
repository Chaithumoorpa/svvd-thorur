import uuid
from datetime import datetime
from io import BytesIO
from typing import Optional
from sqlalchemy.orm import Session
from app.models.donor import Donor
from app.models.finance import PaymentMode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

class DonationReceiptService:
    @staticmethod
    def generate_receipt_number(db: Session) -> str:
        """
        Generates a unique receipt number: DON-YYYYMMDD-XXXX
        """
        today = datetime.now().strftime("%Y%m%d")
        
        # Determine strict sequential ID or random suffix. 
        # For simple uniqueness without strict gaps, consistent length is good.
        suffix = uuid.uuid4().hex[:6].upper()
        return f"DON-{today}-{suffix}"

    @staticmethod
    def generate_receipt_pdf(donor: Donor) -> bytes:
        """
        Generates a PDF receipt for the given donor using ReportLab.
        """
        buffer = BytesIO()
        # Use A5 landscape for receipts (common for receipts)
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A5),
                                rightMargin=30, leftMargin=30,
                                topMargin=30, bottomMargin=30)
        
        styles = getSampleStyleSheet()
        elements = []
        
        # Temple Name Header
        header_style = ParagraphStyle(
            'Header',
            parent=styles['Title'],
            fontSize=22,
            spaceAfter=10,
            textColor=colors.darkred
        )
        elements.append(Paragraph("SVVD Thorur Temple", header_style))
        
        # Sub-header
        sub_header_style = ParagraphStyle(
            'SubHeader',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1, # Center
            spaceAfter=20
        )
        elements.append(Paragraph("Thorur Village, Telangana - 506163", sub_header_style))
        elements.append(Paragraph("Offical Donation Receipt", styles['Heading3']))
        
        elements.append(Spacer(1, 15))
        
        # Receipt Details Table
        data = [
            ["Receipt No:", donor.receipt_number or "N/A", "Date:", donor.receipt_generated_at.strftime('%d-%m-%Y') if donor.receipt_generated_at else datetime.now().strftime('%d-%m-%Y')],
            ["Donor Name:", donor.name, "", ""],
            ["Donated For:", donor.donated_for or "General", "Payment Mode:", donor.payment_mode.value if hasattr(donor.payment_mode, 'value') else "CASH"],
            ["Phone:", donor.phone or "N/A", "", ""],
        ]
        
        # Main Info Table
        t = Table(data, colWidths=[1.2*inch, 2.5*inch, 1*inch, 1.5*inch])
        t.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'), # Left labels
            ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'), # Right labels
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
        ]))
        elements.append(t)
        
        elements.append(Spacer(1, 15))

        # Amount Box
        amount_style = ParagraphStyle(
            'Amount',
            parent=styles['Heading2'],
            fontSize=16,
            alignment=1,
            textColor=colors.black,
            borderWidth=1,
            borderColor=colors.black,
            ipadding=10,
            borderRadius=5
        )
        
        # Currency formatting
        amount_text = f"Amount Received: Rs. {donor.amount}/-"
        elements.append(Paragraph(amount_text, amount_style))
        
        elements.append(Spacer(1, 30))
        
        # Authorized Signature area
        footer_data = [
            ["", "Authorized Signature"],
        ]
        ft = Table(footer_data, colWidths=[3.5*inch, 2.5*inch])
        ft.setStyle(TableStyle([
            ('ALIGN', (1,0), (1,0), 'CENTER'),
            ('TOPPADDING', (0,0), (-1,-1), 20),
            ('LINEABOVE', (1,0), (1,0), 1, colors.black), # Line for signature
        ]))
        elements.append(ft)
        
        # System footer
        elements.append(Spacer(1, 20))
        sys_footer = ParagraphStyle('SysFooter', parent=styles['Normal'], fontSize=7, alignment=1, textColor=colors.grey)
        elements.append(Paragraph("This is a system-generated receipt. No physical signature required.", sys_footer))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
