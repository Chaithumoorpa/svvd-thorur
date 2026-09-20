from datetime import date, datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.finance_repo import FinanceRepository
from io import BytesIO, StringIO
import csv
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def _csv_safe(value):
    """Neutralise spreadsheet formula injection (=, +, -, @ at the start of a text cell)."""
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@", chr(9), chr(13)):
        return "'" + value
    return value


class LedgerService:
    @staticmethod
    def generate_ledger(db: Session, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        # 1. Calculate Opening Balance (Total Income < start_date - Total Expenses < start_date)
        total_income_before = FinanceRepository.get_total_income(db, before_date=start_date)
        total_expenses_before = FinanceRepository.get_total_expenses(db, before_date=start_date)
        opening_balance = total_income_before - total_expenses_before
        
        # 2. Get Transactions in range
        incomes = FinanceRepository.list_income(db, start_date=start_date, end_date=end_date)
        expenses = FinanceRepository.list_expenses(db, start_date=start_date, end_date=end_date)
        
        # 3. Merge and Normalize
        transactions = []
        for i in incomes:
            transactions.append({
                "date": i.received_at, # datetime
                "particulars": f"Income: {i.source_type.value}",
                "voucher_no": str(i.id)[:8], # Short ID for display
                "credit": i.amount,
                "debit": 0,
                "type": "INCOME"
            })
            
        for e in expenses:
            transactions.append({
                "date": e.expense_date, # date
                "particulars": f"Expense: {e.description} ({e.category.value})",
                "voucher_no": str(e.id)[:8],
                "credit": 0,
                "debit": e.amount,
                "type": "EXPENSE"
            })
            
        # 4. Sort Chronologically (ASC)
        # Handle date vs datetime comparison by converting all to datetime or date based on preference.
        # received_at is datetime, expense_date is date.
        # Let's verify comparing them directly works/makes sense or convert.
        # Ideally, we sort by timestamp. Expense only has date, so treat as start of day or end of day? 
        # Usually expenses happen during the day. Let's treat as date.
        
        def get_sort_key(x):
            d = x["date"]
            if isinstance(d, datetime):
                return d.date()
            return d

        transactions.sort(key=get_sort_key)
        
        # 5. Calculate Running Balance
        ledger = []
        
        # Add Opening Balance Row
        ledger.append({
            "date": start_date,
            "particulars": "Opening Balance",
            "voucher_no": "-",
            "credit": 0,
            "debit": 0,
            "balance": opening_balance
        })
        
        current_balance = opening_balance
        
        for t in transactions:
            credit = t["credit"]
            debit = t["debit"]
            current_balance += (credit - debit)
            
            # Format date for display
            row_date = t["date"]
            if isinstance(row_date, datetime):
                row_date_str = row_date.strftime("%Y-%m-%d")
            else:
                row_date_str = row_date.strftime("%Y-%m-%d")

            ledger.append({
                "date": row_date_str,
                "particulars": t["particulars"],
                "voucher_no": t["voucher_no"],
                "credit": credit,
                "debit": debit,
                "balance": current_balance
            })
            
        return ledger

    @staticmethod
    def generate_ledger_csv(ledger_data: List[Dict[str, Any]]) -> str:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["DATE", "PARTICULARS", "VOUCHER NO", "CREDIT", "DEBIT", "BALANCE"])
        
        for row in ledger_data:
            writer.writerow([
                row["date"],
                _csv_safe(row["particulars"]),
                row["voucher_no"],
                row["credit"],
                row["debit"],
                row["balance"]
            ])
            
        return output.getvalue()

    @staticmethod
    def generate_ledger_pdf(ledger_data: List[Dict[str, Any]], start_date: date, end_date: date) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        styles = getSampleStyleSheet()
        elements = []
        
        # Header
        elements.append(Paragraph("SVVD Temple System - Official Ledger", styles['Title']))
        elements.append(Paragraph(f"Period: {start_date} to {end_date}", styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Table Data
        table_data = [["DATE", "PARTICULARS", "VOUCHER NO", "CREDIT", "DEBIT", "BALANCE"]]
        
        for row in ledger_data:
            # Format currency columns
            credit = f"{row['credit']}" if row['credit'] > 0 else ""
            debit = f"{row['debit']}" if row['debit'] > 0 else ""
            
            table_row = [
                str(row["date"]),
                Paragraph(escape(row["particulars"]), styles['Normal']), # Wrap text
                row["voucher_no"],
                credit,
                debit,
                str(row["balance"])
            ]
            table_data.append(table_row)
            
        # Table Style
        t = Table(table_data, colWidths=[80, 250, 80, 60, 60, 80], repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(t)
        
        # Closing Balance Footer
        elements.append(Spacer(1, 20))
        closing_balance = ledger_data[-1]["balance"] if ledger_data else 0
        elements.append(Paragraph(f"Closing Balance: Rs. {closing_balance}/-", styles['Heading3']))
        
        # Footer
        elements.append(Spacer(1, 30))
        footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=1, textColor=colors.grey)
        elements.append(Paragraph("Generated by SVVD Temple System", footer_style))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
