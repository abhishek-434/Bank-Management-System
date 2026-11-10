"""Transaction history and financial ledger view with CSV and PDF exports."""
from datetime import datetime
from tkinter import messagebox, filedialog
import customtkinter as ctk
from ui.theme import Theme
from ui.components.data_table import DataTable
from ui.components.modal import ReceiptModal
from services.transaction_service import transaction_service
from services.report_service import report_service
from services.pdf_service import pdf_service
from services.account_service import account_service
from services.auth_service import SessionContext
from utils.formatters import format_currency
from config.settings import settings


class TransactionHistoryView(ctk.CTkFrame):
    """Complete financial ledger inspection view supporting multi-column filtering and document exports."""

    def __init__(self, master, current_session: SessionContext, **kwargs):
        super().__init__(master, fg_color=Theme.BG_DARK, **kwargs)

        self.current_session = current_session
        self.type_filter = "ALL"
        self.current_account_filter = None

        self._build_ui()
        self.refresh_transactions()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(16, 12))

        title_lbl = ctk.CTkLabel(
            header,
            text="Transaction History & Ledger",
            font=Theme.font_title(),
            text_color=Theme.TEXT_PRIMARY,
        )
        title_lbl.pack(side="left")

        # Export buttons
        btn_box = ctk.CTkFrame(header, fg_color="transparent")
        btn_box.pack(side="right")

        csv_btn = ctk.CTkButton(
            btn_box,
            text="Export to CSV",
            height=34,
            font=Theme.font_body_bold(),
            fg_color=Theme.SURFACE_CARD,
            hover_color=Theme.SURFACE_NAV,
            border_color=Theme.BORDER,
            border_width=1,
            corner_radius=8,
            command=self._export_csv,
        )
        csv_btn.pack(side="left", padx=4)

        # Filters toolbar
        filter_bar = ctk.CTkFrame(self, fg_color=Theme.SURFACE_CARD, corner_radius=8)
        filter_bar.pack(fill="x", padx=24, pady=(0, 12))

        ctk.CTkLabel(filter_bar, text="Filter by Type:", font=Theme.font_small(), text_color=Theme.TEXT_SECONDARY).pack(side="left", padx=(14, 6), pady=8)

        types = [
            "ALL",
            "DEPOSIT",
            "WITHDRAWAL",
            "TRANSFER_DEBIT",
            "TRANSFER_CREDIT",
            "LOAN_DISBURSEMENT",
            "LOAN_REPAYMENT",
        ]
        type_menu = ctk.CTkOptionMenu(
            filter_bar,
            values=types,
            height=30,
            font=Theme.font_small(),
            fg_color=Theme.SURFACE_INPUT,
            button_color=Theme.ACCENT_BLUE,
            corner_radius=6,
            command=self._on_type_change,
        )
        type_menu.pack(side="left", padx=4, pady=8)

        # Table
        table_container = ctk.CTkFrame(self, fg_color="transparent")
        table_container.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        columns = ["Ref Number", "Account No", "Type", "Amount", "Balance After", "Status", "Timestamp"]
        col_widths = [140, 110, 120, 100, 100, 80, 130]

        self.table = DataTable(
            table_container,
            columns=columns,
            col_widths=col_widths,
            search_placeholder="Search by reference or account number...",
            on_search=self._on_search,
            on_row_click=self._on_row_click,
        )
        self.table.pack(fill="both", expand=True)

    def refresh_transactions(self, query: str = ""):
        # Determine customer scoping
        customer_id = self.current_session.customer_id if self.current_session.is_customer else None
        account_no = query.strip() if (query.strip().isdigit() and len(query.strip()) >= 5) else None

        txns = transaction_service.search_transactions(
            customer_id=customer_id,
            account_number=account_no,
            transaction_type=self.type_filter,
            limit=200,
        )

        rows = []
        for t in txns:
            # Local query search match
            if query and not account_no:
                q = query.lower()
                matches = (
                    q in t.reference_no.lower()
                    or (t.account and q in t.account.account_number.lower())
                    or (t.description and q in t.description.lower())
                )
                if not matches:
                    continue

            rows.append({
                "raw_txn": t,
                "Ref Number": t.reference_no,
                "Account No": t.account.account_number if t.account else "N/A",
                "Type": t.transaction_type,
                "Amount": format_currency(t.amount),
                "Balance After": format_currency(t.new_balance),
                "Status": t.status,
                "status": t.status,
                "Timestamp": t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else "",
            })

        self.table.set_data(
            rows,
            key_fields=["Ref Number", "Account No", "Type", "Amount", "Balance After", "Status", "Timestamp"],
        )

    def _on_type_change(self, val: str):
        self.type_filter = val
        self.refresh_transactions()

    def _on_search(self, query: str):
        self.refresh_transactions(query)

    def _on_row_click(self, row_data):
        t = row_data.get("raw_txn")
        if not t:
            return

        receipt = {
            "receipt_type": t.transaction_type,
            "reference_no": t.reference_no,
            "account_number": t.account.account_number if t.account else "N/A",
            "customer_name": t.account.customer.full_name if (t.account and t.account.customer) else "N/A",
            "amount": t.amount,
            "previous_balance": t.previous_balance,
            "new_balance": t.new_balance,
            "description": t.description,
            "status": t.status,
            "timestamp": t.created_at,
        }
        ReceiptModal(self, receipt)

    def _export_csv(self):
        default_file = f"Transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        dest = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Spreadsheet", "*.csv")],
            initialdir=str(settings.EXPORTS_DIR),
            initialfile=default_file,
        )
        if dest:
            try:
                report_service.export_transactions_to_csv(dest)
                messagebox.showinfo("Export Complete", f"Transactions successfully exported to:\n{dest}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Failed to export CSV:\n{e}")

