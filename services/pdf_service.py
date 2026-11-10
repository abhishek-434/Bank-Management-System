"""PDF generation service for official transaction receipts and bank statements."""
import logging
from decimal import Decimal
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from utils.formatters import format_currency, format_datetime

logger = logging.getLogger("bms.pdf_service")


class PdfService:
    """Generates financial PDF documents using ReportLab."""

    @staticmethod
    def generate_receipt_pdf(receipt: Dict[str, Any], output_path: str) -> str:
        """Generate a sleek, formatted PDF transaction receipt."""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0B132B"),
            alignment=1,
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#4A5568"),
            alignment=1,
        )
        cell_bold = ParagraphStyle(
            "CellBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=12,
            textColor=colors.HexColor("#1A202C"),
        )
        cell_val = ParagraphStyle(
            "CellVal",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=12,
            textColor=colors.HexColor("#2D3748"),
        )
        amount_style = ParagraphStyle(
            "AmountVal",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=18,
            textColor=colors.HexColor("#0077B6"),
            alignment=2,
        )

        elements = []

        # Header
        elements.append(Paragraph("APEX HORIZON BANK", title_style))
        elements.append(Paragraph("Core Banking Management System • Official Transaction Receipt", subtitle_style))
        elements.append(Spacer(1, 15))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0077B6"), spaceAfter=15))

        # Receipt Data Table
        ref_no = receipt.get("reference_no") or receipt.get("transfer_reference", "N/A")
        ts = receipt.get("timestamp")
        ts_str = format_datetime(ts) if isinstance(ts, datetime) else str(ts)

        table_data = [
            [Paragraph("Receipt Type:", cell_bold), Paragraph(str(receipt.get("receipt_type", "TRANSACTION")), cell_val)],
            [Paragraph("Transaction Reference:", cell_bold), Paragraph(str(ref_no), cell_bold)],
            [Paragraph("Date & Time (UTC):", cell_bold), Paragraph(ts_str, cell_val)],
            [Paragraph("Transaction Status:", cell_bold), Paragraph(str(receipt.get("status", "SUCCESS")), cell_bold)],
        ]

        if "account_number" in receipt:
            table_data.append([Paragraph("Account Number:", cell_bold), Paragraph(str(receipt["account_number"]), cell_val)])
        if "customer_name" in receipt:
            table_data.append([Paragraph("Customer Name:", cell_bold), Paragraph(str(receipt["customer_name"]), cell_val)])
        if "sender_account" in receipt:
            table_data.append([Paragraph("Sender Account:", cell_bold), Paragraph(f"{receipt['sender_account']} ({receipt.get('sender_name', '')})", cell_val)])
        if "receiver_account" in receipt:
            table_data.append([Paragraph("Beneficiary Account:", cell_bold), Paragraph(f"{receipt['receiver_account']} ({receipt.get('receiver_name', '')})", cell_val)])

        table_data.append([Paragraph("Description:", cell_bold), Paragraph(str(receipt.get("description", "N/A")), cell_val)])

        amt = receipt.get("amount", Decimal("0.00"))
        table_data.append([
            Paragraph("Total Amount:", cell_bold),
            Paragraph(format_currency(amt), amount_style),
        ])

        if "new_balance" in receipt:
            table_data.append([
                Paragraph("Closing Balance:", cell_bold),
                Paragraph(format_currency(receipt["new_balance"]), cell_bold),
            ])

        t = Table(table_data, colWidths=[2.2 * inch, 4.8 * inch])
        t.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("PADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ])
        )
        elements.append(t)
        elements.append(Spacer(1, 25))

        # Footer notice
        footer_style = ParagraphStyle(
            "FooterNotice",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            textColor=colors.HexColor("#718096"),
            alignment=1,
        )
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E0"), spaceAfter=10))
        elements.append(Paragraph("This is an electronically generated receipt from an educational banking simulation.", footer_style))
        elements.append(Paragraph("No physical signature is required. Keep this copy for your personal records.", footer_style))

        doc.build(elements)
        logger.info(f"Receipt PDF generated successfully at {output_path}")
        return output_path

    @staticmethod
    def generate_statement_pdf(
        account_data: Dict[str, Any],
        transactions: List[Any],
        output_path: str,
    ) -> str:
        """Generate a complete bank account statement PDF."""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "StmtTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            textColor=colors.HexColor("#0B132B"),
            alignment=0,
        )
        cell_header = ParagraphStyle(
            "CellHdr",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=colors.white,
            alignment=1,
        )
        cell_body = ParagraphStyle(
            "CellBdy",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7,
            textColor=colors.HexColor("#2D3748"),
        )

        elements = []

        # Title
        elements.append(Paragraph("APEX HORIZON BANK • OFFICIAL ACCOUNT STATEMENT", title_style))
        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0077B6"), spaceAfter=12))

        # Account details summary
        info_data = [
            [
                f"Account Number: {account_data.get('account_number', 'N/A')}",
                f"Account Holder: {account_data.get('customer_name', 'N/A')}",
            ],
            [
                f"Account Type: {account_data.get('account_type', 'N/A')}",
                f"Current Balance: {format_currency(account_data.get('current_balance', 0))}",
            ],
            [
                f"Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Status: {account_data.get('status', 'ACTIVE')}",
            ],
        ]
        info_table = Table(info_data, colWidths=[3.5 * inch, 3.5 * inch])
        info_table.setStyle(
            TableStyle([
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1A202C")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("PADDING", (0, 0), (-1, -1), 4),
            ])
        )
        elements.append(info_table)
        elements.append(Spacer(1, 15))

        # Transactions table
        headers = ["Ref No", "Date", "Type", "Description", "Amount", "Balance"]
        table_rows = [[Paragraph(h, cell_header) for h in headers]]

        for txn in transactions:
            ts_str = txn.created_at.strftime("%Y-%m-%d %H:%M") if hasattr(txn, "created_at") and txn.created_at else ""
            table_rows.append([
                Paragraph(str(getattr(txn, "reference_no", "")), cell_body),
                Paragraph(ts_str, cell_body),
                Paragraph(str(getattr(txn, "transaction_type", "")), cell_body),
                Paragraph(str(getattr(txn, "description", ""))[:30], cell_body),
                Paragraph(format_currency(getattr(txn, "amount", 0)), cell_body),
                Paragraph(format_currency(getattr(txn, "new_balance", 0)), cell_body),
            ])

        if len(table_rows) == 1:
            table_rows.append([Paragraph("No transactions recorded for this account.", cell_body)] * 6)

        tx_table = Table(table_rows, colWidths=[1.4 * inch, 1.1 * inch, 1.1 * inch, 1.6 * inch, 0.9 * inch, 0.9 * inch])
        tx_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B132B")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("PADDING", (0, 0), (-1, -1), 4),
            ])
        )
        elements.append(tx_table)
        elements.append(Spacer(1, 20))

        # Footer notice
        footer_style = ParagraphStyle(
            "StmtFoot",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            textColor=colors.HexColor("#718096"),
            alignment=1,
        )
        elements.append(Paragraph("Apex Horizon Bank • Educational Simulation Ledger • End of Statement", footer_style))

        doc.build(elements)
        logger.info(f"Statement PDF generated successfully at {output_path}")
        return output_path


pdf_service = PdfService()

