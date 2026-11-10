"""Bank account management and lifecycle view."""
from decimal import Decimal
from tkinter import messagebox, filedialog
import customtkinter as ctk
from ui.theme import Theme
from ui.components.data_table import DataTable
from ui.components.modal import ConfirmModal
from services.account_service import account_service
from services.customer_service import customer_service
from services.transaction_service import transaction_service
from services.pdf_service import pdf_service
from services.auth_service import SessionContext
from utils.formatters import format_currency
from config.settings import settings


class AccountMgmtView(ctk.CTkFrame):
    """Account management interface supporting account opening, lifecycle changes, and statement exports."""

    def __init__(self, master, current_session: SessionContext, **kwargs):
        super().__init__(master, fg_color=Theme.BG_DARK, **kwargs)

        self.current_session = current_session
        self.type_filter = "ALL"
        self.status_filter = "ALL"

        self._build_ui()
        self.refresh_accounts()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(16, 12))

        title_lbl = ctk.CTkLabel(
            header,
            text="Bank Accounts",
            font=Theme.font_title(),
            text_color=Theme.TEXT_PRIMARY,
        )
        title_lbl.pack(side="left")

        # Open Account button (Staff & Admin only)
        if not self.current_session.is_customer:
            open_btn = ctk.CTkButton(
                header,
                text="+ Open New Account",
                height=36,
                font=Theme.font_body_bold(),
                fg_color=Theme.ACCENT_BLUE,
                hover_color=Theme.ACCENT_CYAN_HOVER,
                corner_radius=8,
                command=self._open_new_account_modal,
            )
            open_btn.pack(side="right")

        # Table
        table_container = ctk.CTkFrame(self, fg_color="transparent")
        table_container.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        columns = ["Account Number", "Account Holder", "Product Type", "Current Balance", "Status", "Opened On"]
        col_widths = [140, 160, 130, 120, 90, 110]

        self.table = DataTable(
            table_container,
            columns=columns,
            col_widths=col_widths,
            search_placeholder="Search by account number or customer name...",
            on_search=self._on_search,
            on_row_click=self._on_row_click,
        )
        self.table.pack(fill="both", expand=True)

    def refresh_accounts(self, query: str = ""):
        # If logged in as customer, only show their accounts
        if self.current_session.is_customer and self.current_session.customer_id:
            accounts = account_service.list_by_customer(self.current_session.customer_id)
        else:
            accounts = account_service.list_all_accounts(
                search_query=query,
                type_filter=self.type_filter,
                status_filter=self.status_filter,
            )

        rows = [
            {
                "id": a.id,
                "Account Number": a.account_number,
                "Account Holder": a.customer.full_name if a.customer else "N/A",
                "Product Type": a.account_type.name if a.account_type else "Standard",
                "Current Balance": format_currency(a.current_balance),
                "Status": a.status,
                "status": a.status,
                "Opened On": a.opened_at.strftime("%Y-%m-%d") if a.opened_at else "",
            }
            for a in accounts
        ]
        self.table.set_data(
            rows,
            key_fields=["Account Number", "Account Holder", "Product Type", "Current Balance", "Status", "Opened On"],
        )

    def _on_search(self, query: str):
        self.refresh_accounts(query)

    def _on_row_click(self, row_data):
        acct_id = row_data.get("id")
        if acct_id:
            self._open_account_details_modal(acct_id)

    def _open_new_account_modal(self):
        """Modal to open a new savings/current/fixed deposit account."""
        modal = ctk.CTkToplevel(self)
        modal.title("Open New Bank Account - Apex Horizon Bank")
        modal.geometry("500x520")
        modal.resizable(False, False)
        modal.configure(fg_color=Theme.BG_DARK)
        modal.transient(self)
        modal.grab_set()

        container = ctk.CTkFrame(modal, fg_color=Theme.SURFACE_CARD, corner_radius=12)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text="Open Bank Account", font=Theme.font_subtitle(), text_color=Theme.TEXT_PRIMARY).pack(pady=(16, 12))

        form = ctk.CTkFrame(container, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20)

        # 1. Customer Selection
        customers = customer_service.search_customers()
        cust_map = {f"{c.customer_code} - {c.full_name}": c.id for c in customers}
        cust_options = list(cust_map.keys()) or ["No registered customers"]

        ctk.CTkLabel(form, text="Select Customer *", font=Theme.font_small(), text_color=Theme.TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(4, 2))
        cust_dropdown = ctk.CTkOptionMenu(
            form,
            values=cust_options,
            height=36,
            font=Theme.font_body(),
            fg_color=Theme.SURFACE_INPUT,
            button_color=Theme.ACCENT_BLUE,
            corner_radius=8,
        )
        cust_dropdown.pack(fill="x", pady=(0, 10))

        # 2. Account Type Selection
        types = account_service.get_account_types()
        type_map = {f"{t.name} (Min: ${t.minimum_balance:.2f})": t.code for t in types}
        type_options = list(type_map.keys())

        ctk.CTkLabel(form, text="Account Product Type *", font=Theme.font_small(), text_color=Theme.TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(4, 2))
        type_dropdown = ctk.CTkOptionMenu(
            form,
            values=type_options,
            height=36,
            font=Theme.font_body(),
            fg_color=Theme.SURFACE_INPUT,
            button_color=Theme.ACCENT_BLUE,
            corner_radius=8,
        )
        type_dropdown.pack(fill="x", pady=(0, 10))

        # 3. Initial Deposit Amount
        ctk.CTkLabel(form, text="Initial Deposit Amount ($) *", font=Theme.font_small(), text_color=Theme.TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(4, 2))
        deposit_entry = ctk.CTkEntry(
            form,
            placeholder_text="e.g. 500.00",
            height=36,
            font=Theme.font_body(),
            fg_color=Theme.SURFACE_INPUT,
            border_color=Theme.BORDER,
            corner_radius=8,
        )
        deposit_entry.pack(fill="x", pady=(0, 14))
        deposit_entry.insert(0, "500.00")

        err_lbl = ctk.CTkLabel(form, text="", font=Theme.font_small(), text_color=Theme.DANGER)
        err_lbl.pack(pady=4)

        def save_account():
            err_lbl.configure(text="")
            selected_cust_str = cust_dropdown.get()
            selected_type_str = type_dropdown.get()

            cust_id = cust_map.get(selected_cust_str)
            type_code = type_map.get(selected_type_str)

            if not cust_id:
                err_lbl.configure(text="Please select a valid customer.")
                return

            try:
                amt = Decimal(deposit_entry.get().strip().replace(",", ""))
            except Exception:
                err_lbl.configure(text="Invalid deposit amount.")
                return

            ok, acct, msg = account_service.open_account(
                customer_id=cust_id,
                account_type_code=type_code,
                initial_deposit=amt,
                created_by_user_id=self.current_session.user_id,
            )
            if ok:
                messagebox.showinfo("Account Created", f"Account {acct.account_number} created successfully!")
                modal.destroy()
                self.refresh_accounts()
            else:
                err_lbl.configure(text=msg)

        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=16)

        ctk.CTkButton(btn_row, text="Confirm & Open Account", height=38, fg_color=Theme.SUCCESS, hover_color=Theme.SUCCESS_HOVER, font=Theme.font_body_bold(), corner_radius=8, command=save_account).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(btn_row, text="Cancel", height=38, fg_color="transparent", border_color=Theme.BORDER, border_width=1, font=Theme.font_body(), corner_radius=8, command=modal.destroy).pack(side="right", fill="x", expand=True, padx=(6, 0))

    def _open_account_details_modal(self, account_id: str):
        """Modal showing full account details, statement generator, and status options."""
        acct = account_service.get_by_id(account_id)
        if not acct:
            return

        modal = ctk.CTkToplevel(self)
        modal.title(f"Account Details - {acct.account_number}")
        modal.geometry("540x580")
        modal.resizable(False, False)
        modal.configure(fg_color=Theme.BG_DARK)
        modal.transient(self)
        modal.grab_set()

        container = ctk.CTkFrame(modal, fg_color=Theme.SURFACE_CARD, corner_radius=12)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text=f"Account {acct.account_number}", font=Theme.font_subtitle(), text_color=Theme.TEXT_PRIMARY).pack(pady=(16, 2))
        ctk.CTkLabel(container, text=f"{acct.account_type.name} • {acct.status}", font=Theme.font_small(), text_color=Theme.ACCENT_CYAN).pack(pady=(0, 12))

        # Balance display
        bal_box = ctk.CTkFrame(container, fg_color=Theme.SURFACE_NAV, corner_radius=8)
        bal_box.pack(fill="x", padx=16, pady=8)

        ctk.CTkLabel(bal_box, text="CURRENT AVAILABLE BALANCE", font=Theme.font_small(), text_color=Theme.TEXT_MUTED).pack(pady=(8, 2))
        ctk.CTkLabel(bal_box, text=format_currency(acct.current_balance), font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=24, weight="bold"), text_color=Theme.SUCCESS).pack(pady=(0, 8))

        # Details list
        fields = [
            ("Account Holder", acct.customer.full_name if acct.customer else "N/A"),
            ("Minimum Balance", format_currency(acct.account_type.minimum_balance)),
            ("Interest Rate", f"{acct.account_type.interest_rate}% p.a."),
            ("Withdrawal Limit", format_currency(acct.account_type.daily_withdrawal_limit)),
            ("Opened Date", acct.opened_at.strftime("%Y-%m-%d %H:%M")),
        ]
        info_frame = ctk.CTkFrame(container, fg_color=Theme.SURFACE_NAV, corner_radius=8)
        info_frame.pack(fill="x", padx=16, pady=8)

        for k, v in fields:
            row = ctk.CTkFrame(info_frame, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=4)
            ctk.CTkLabel(row, text=k, width=130, font=Theme.font_small(), text_color=Theme.TEXT_SECONDARY, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=str(v), font=Theme.font_body_bold(), text_color=Theme.TEXT_PRIMARY, anchor="w").pack(side="left")

        # Action Buttons
        btn_box = ctk.CTkFrame(container, fg_color="transparent")
        btn_box.pack(fill="x", padx=16, pady=16)

        # PDF Statement
        def export_statement():
            txns = transaction_service.search_transactions(account_number=acct.account_number, limit=200)
            dest = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF Document", "*.pdf")],
                initialdir=str(settings.STATEMENTS_DIR),
                initialfile=f"Statement_{acct.account_number}.pdf",
            )
            if dest:
                try:
                    account_data = {
                        "account_number": acct.account_number,
                        "customer_name": acct.customer.full_name if acct.customer else "N/A",
                        "account_type": acct.account_type.name,
                        "current_balance": acct.current_balance,
                        "status": acct.status,
                    }
                    pdf_service.generate_statement_pdf(account_data, txns, dest)
                    messagebox.showinfo("Statement Saved", f"Official bank statement PDF saved to:\n{dest}")
                except Exception as e:
                    messagebox.showerror("Export Failed", f"Could not create statement:\n{e}")

        ctk.CTkButton(btn_box, text="Download PDF Statement", fg_color=Theme.ACCENT_BLUE, hover_color=Theme.ACCENT_CYAN_HOVER, corner_radius=8, command=export_statement).pack(fill="x", pady=3)

        # Admin & Employee Lifecycle Controls (Freeze / Close)
        if not self.current_session.is_customer:
            ctrl_row = ctk.CTkFrame(btn_box, fg_color="transparent")
            ctrl_row.pack(fill="x", pady=4)

            def toggle_freeze():
                new_st = "ACTIVE" if acct.status == "FROZEN" else "FROZEN"
                ok, msg = account_service.set_status(acct.id, new_st, self.current_session.user_id)
                if ok:
                    messagebox.showinfo("Status Updated", msg)
                    modal.destroy()
                    self.refresh_accounts()
                else:
                    messagebox.showerror("Error", msg)

            def close_account():
                ConfirmModal(
                    self,
                    title="Close Bank Account",
                    message=(
                        f"Are you sure you want to permanently close account {acct.account_number}?\n\n"
                        "Account balance must be $0.00 and no active loans must exist."
                    ),
                    is_destructive=True,
                    on_confirm=lambda: self._do_close(acct.id, modal),
                )

            frz_text = "Unfreeze Account" if acct.status == "FROZEN" else "Freeze Account"
            frz_color = Theme.SUCCESS if acct.status == "FROZEN" else Theme.WARNING
            ctk.CTkButton(ctrl_row, text=frz_text, fg_color=frz_color, corner_radius=8, command=toggle_freeze).pack(side="left", fill="x", expand=True, padx=(0, 4))

            if acct.status != "CLOSED":
                ctk.CTkButton(ctrl_row, text="Close Account", fg_color=Theme.DANGER, hover_color=Theme.DANGER_HOVER, corner_radius=8, command=close_account).pack(side="right", fill="x", expand=True, padx=(4, 0))

    def _do_close(self, account_id: str, parent_modal):
        ok, msg = account_service.set_status(account_id, "CLOSED", self.current_session.user_id)
        if ok:
            messagebox.showinfo("Account Closed", msg)
            parent_modal.destroy()
            self.refresh_accounts()
        else:
            messagebox.showerror("Closure Denied", msg)

