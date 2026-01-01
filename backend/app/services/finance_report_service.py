from datetime import date, datetime
import calendar
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.finance import IncomeTransaction, ExpenseTransaction
from app.repositories.finance_repo import FinanceRepository

class FinanceReportService:
    @staticmethod
    def _get_date_range(year: int, month: int):
        _, last_day = calendar.monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)
        return start_date, end_date

    @staticmethod
    def generate_monthly_json(db: Session, year: int, month: int) -> Dict[str, Any]:
        start_date, end_date = FinanceReportService._get_date_range(year, month)
        
        # Get raw transactions
        incomes = FinanceRepository.list_income(db, start_date, end_date)
        expenses = FinanceRepository.list_expenses(db, start_date, end_date)
        
        # Calculate totals
        total_income = sum(i.amount for i in incomes)
        total_expenses = sum(e.amount for e in expenses)
        net_balance = total_income - total_expenses
        
        # Breakdown by Source
        income_breakdown = {}
        for i in incomes:
            source = i.source_type.value
            income_breakdown[source] = income_breakdown.get(source, 0) + i.amount
            
        # Breakdown by Category
        expense_breakdown = {}
        for e in expenses:
            cat = e.category.value
            expense_breakdown[cat] = expense_breakdown.get(cat, 0) + e.amount
            
        return {
            "month": start_date.strftime("%B %Y"),
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_balance": net_balance,
            "income_breakdown": income_breakdown,
            "expense_breakdown": expense_breakdown
        }

    @staticmethod
    def generate_monthly_pdf(db: Session, year: int, month: int) -> bytes:
        data = FinanceReportService.generate_monthly_json(db, year, month)
        
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from io import BytesIO

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=18,
            alignment=1, # Center
            spaceAfter=20
        )
        elements.append(Paragraph("SVVD Thorur Temple - Monthly Financial Report", title_style))
        elements.append(Paragraph(f"Period: {data['month']}", styles['Heading2']))
        elements.append(Spacer(1, 20))

        # Summary Table
        summary_data = [
            ["Metric", "Amount (INR)"],
            ["Total Income", f"Rs. {data['total_income']:,}"],
            ["Total Expenses", f"Rs. {data['total_expenses']:,}"],
            ["Net Balance", f"Rs. {data['net_balance']:,}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[200, 200])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 30))

        # Income Breakdown
        elements.append(Paragraph("Income Breakdown", styles['Heading2']))
        income_rows = [["Source", "Amount"]]
        for source, amount in data['income_breakdown'].items():
            income_rows.append([source, f"Rs. {amount:,}"])
            
        if len(income_rows) > 1:
            t = Table(income_rows, colWidths=[200, 200])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (1, 0), colors.lightgreen),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(t)
        else:
             elements.append(Paragraph("No income recorded.", styles['Normal']))
             
        elements.append(Spacer(1, 20))

        # Expense Breakdown
        elements.append(Paragraph("Expense Breakdown", styles['Heading2']))
        expense_rows = [["Category", "Amount"]]
        for cat, amount in data['expense_breakdown'].items():
            expense_rows.append([cat, f"Rs. {amount:,}"])
            
        if len(expense_rows) > 1:
            t = Table(expense_rows, colWidths=[200, 200])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (1, 0), colors.lightpink),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(t)
        else:
             elements.append(Paragraph("No expenses recorded.", styles['Normal']))

        # Footer
        elements.append(Spacer(1, 50))
        footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=1, textColor=colors.grey)
        elements.append(Paragraph("CONFIDENTIAL - For Trustee Review Only", footer_style))
        elements.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", footer_style))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
