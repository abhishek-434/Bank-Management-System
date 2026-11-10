"""Deposit transaction workflow view."""
from decimal import Decimal
from tkinter import messagebox
import customtkinter as ctk
from ui.theme import Theme
from ui.components.modal import ReceiptModal
from services.transaction_service import transaction_service
from services.account_service import account_service
from services.auth_service import SessionContext
from utils.formatters import format_currency


class DepositView(ctk.CTkFrame):
    """Secure deposit interface with instant account verification and receipt generation."""

    def __init__(self, master, current_session: SessionContext, **kwargs):
        super().__init__(master, fg_color=Theme.BG_DARK, **kwargs)

        self.current_session = current_session
        self.selected_account = None

        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(16, 12))

        title_lbl = ctk.CTkLabel(
            header,
            text="Cash & Electronic Deposit",
            font=Theme.font_title(),
            text_color=Theme.TEXT_PRIMARY,
        )
        title_lbl.pack(side="left")

        # Main Card Form
        card = ctk.CTkFrame(self, fg_color=Theme.SURFACE_CARD, border_color=Theme.BORDER, border_width=1, corner_radius=12)
        card.pack(fill="x", padx=24, pady=10)

        ctk.CTkLabel(card, text="Deposit Form", font=Theme.font_subtitle(), text_color=Theme.TEXT_PRIMARY).pack(padx=20, pady=(16, 8), anchor="w")

        # Step 1: Account Number Lookup
        acct_box = ctk.CTkFrame(card, fg_color="transparent")
        acct_box.pack(fill="x", padx=20, pady=6)

        ctk.CTkLabel(acct_box, text="Account Number *", font=Theme.font_small(), text_color=Theme.TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(0, 2))

        search_row = ctk.CTkFrame(acct_box, fg_color="transparent")
        search_row.pack(fill="x")

        self.account_entry = ctk.CTkEntry(
            search_row,
            placeholder_text="Enter 10-digit account number (e.g. 1008472910)",
            height=38,
            font=Theme.font_body(),
            fg_color=Theme.SURFACE_INPUT,
            border_color=Theme.BORDER,
            corner_radius=8,
        )
        self.account_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        lookup_btn = ctk.CTkButton(
            search_row,
            text="Verify Account",
            width=120,
            height=38,
            font=Theme.font_body_bold(),
            fg_color=Theme.ACCENT_BLUE,
            hover_color=Theme.ACCENT_CYAN_HOVER,
            corner_radius=8,
            command=self._lookup_account,
        )
        lookup_btn.pack(side="right")

        # Verified Account Card
        self.info_card = ctk.CTkFrame(card, fg_color=Theme.SURFACE_NAV, corner_radius=8)
        self.info_card.pack(fill="x", padx=20, pady=8)

        self.info_lbl = ctk.CTkLabel(
            self.info_card,
            text="Please enter and verify an account number above.",
            font=Theme.font_body(),
            text_color=Theme.TEXT_MUTED,
        )
        self.info_lbl.pack(padx=16, pady=14)

        # Step 2: Deposit Amount & Description
        inputs_box = ctk.CTkFrame(card, fg_color="transparent")
        inputs_box.pack(fill="x", padx=20, pady=6)

        ctk.CTkLabel(inputs_box, text="Deposit Amount ($) *", font=Theme.font_small(), text_color=Theme.TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(0, 2))
        self.amount_entry = ctk.CTkEntry(
            inputs_box,
            placeholder_text="0.00",
            height=38,
            font=Theme.font_body(),
            fg_color=Theme.SURFACE_INPUT,
            border_color=Theme.BORDER,
            corner_radius=8,
        )
        self.amount_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(inputs_box, text="Transaction Note / Description", font=Theme.font_small(), text_color=Theme.TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(0, 2))
        self.desc_entry = ctk.CTkEntry(
            inputs_box,
            placeholder_text="Deposit via Branch Counter",
            height=38,
            font=Theme.font_body(),
            fg_color=Theme.SURFACE_INPUT,
            border_color=Theme.BORDER,
            corner_radius=8,
        )
        self.desc_entry.pack(fill="x", pady=(0, 14))

        # Status & Action
        self.status_lbl = ctk.CTkLabel(card, text="", font=Theme.font_small(), text_color=Theme.DANGER)
        self.status_lbl.pack(pady=2)

        self.submit_btn = ctk.CTkButton(
            card,
            text="Process Deposit & Generate Receipt",
            height=42,
            font=Theme.font_body_bold(),
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS_HOVER,
            corner_radius=8,
            command=self._execute_deposit,
        )
        self.submit_btn.pack(fill="x", padx=20, pady=(4, 20))

    def _lookup_account(self):
        acct_no = self.account_entry.get().strip()
        self.status_lbl.configure(text="")
        if not acct_no:
            self.status_lbl.configure(text="Please enter an account number.")
            return

        acct = account_service.get_by_number(acct_no)
        if not acct:
            self.selected_account = None
            self.info_lbl.configure(text=f"Account '{acct_no}' not found.", text_color=Theme.DANGER)
            return

        self.selected_account = acct
        status_color = Theme.SUCCESS if acct.is_operational() else Theme.DANGER
        self.info_lbl.configure(
            text=(
                f"Account Holder: {acct.customer.full_name}  •  "
                f"Product: {acct.account_type.name}  •  "
                f"Balance: {format_currency(acct.current_balance)}  •  "
                f"Status: {acct.status}"
            ),
            text_color=status_color,
        )

    def _execute_deposit(self):
        self.status_lbl.configure(text="")
        if not self.selected_account:
            self._lookup_account()
            if not self.selected_account:
                self.status_lbl.configure(text="Please verify a valid account first.")
                return

        amt_str = self.amount_entry.get().strip()
        desc = self.desc_entry.get().strip() or "Counter Deposit"

        ok, receipt, msg = transaction_service.deposit(
            account_number=self.selected_account.account_number,
            amount_input=amt_str,
            description=desc,
            user_id=self.current_session.user_id,
        )

        if ok and receipt:
            self.amount_entry.delete(0, "end")
            self.desc_entry.delete(0, "end")
            self._lookup_account()  # Refresh balance
            ReceiptModal(self, receipt)
        else:
            self.status_lbl.configure(text=msg)

