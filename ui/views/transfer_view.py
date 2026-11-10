"""Internal account-to-account transfer view."""
from decimal import Decimal
from tkinter import messagebox
import customtkinter as ctk
from ui.theme import Theme
from ui.components.modal import ReceiptModal, ConfirmModal
from services.transaction_service import transaction_service
from services.account_service import account_service
from services.auth_service import SessionContext
from utils.formatters import format_currency


class TransferView(ctk.CTkFrame):
    """Account-to-account fund transfer interface with double-entry atomic processing."""

    def __init__(self, master, current_session: SessionContext, **kwargs):
        super().__init__(master, fg_color=Theme.BG_DARK, **kwargs)

        self.current_session = current_session
        self.sender_account = None
        self.receiver_account = None

        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(16, 12))

        title_lbl = ctk.CTkLabel(
            header,
            text="Internal Account Transfer",
            font=Theme.font_title(),
            text_color=Theme.TEXT_PRIMARY,
        )
        title_lbl.pack(side="left")

        # Main Card Form
        card = ctk.CTkFrame(self, fg_color=Theme.SURFACE_CARD, border_color=Theme.BORDER, border_width=1, corner_radius=12)
        card.pack(fill="x", padx=24, pady=10)

        ctk.CTkLabel(card, text="Direct Account Transfer", font=Theme.font_subtitle(), text_color=Theme.TEXT_PRIMARY).pack(padx=20, pady=(16, 8), anchor="w")

        # 1. Sender Account
        sender_box = ctk.CTkFrame(card, fg_color="transparent")
        sender_box.pack(fill="x", padx=20, pady=4)

        ctk.CTkLabel(sender_box, text="Source / Sender Account *", font=Theme.font_small(), text_color=Theme.TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(0, 2))

        # If customer, provide dropdown of own accounts
        if self.current_session.is_customer and self.current_session.customer_id:
            cust_accts = account_service.list_by_customer(self.current_session.customer_id)
            opts = [f"{a.account_number} - {a.account_type.name} (Bal: ${a.current_balance:,.2f})" for a in cust_accts]
            self.sender_dropdown = ctk.CTkOptionMenu(
                sender_box,
                values=opts or ["No accounts found"],
                height=38,
                font=Theme.font_body(),
                fg_color=Theme.SURFACE_INPUT,
                button_color=Theme.ACCENT_BLUE,
                corner_radius=8,
                command=self._on_customer_sender_select,
            )
            self.sender_dropdown.pack(fill="x")
            self.sender_entry = None
            if cust_accts:
                self.sender_account = cust_accts[0]
        else:
            s_row = ctk.CTkFrame(sender_box, fg_color="transparent")
            s_row.pack(fill="x")
            self.sender_entry = ctk.CTkEntry(
                s_row,
                placeholder_text="Enter sender account number (e.g. 1008472910)",
                height=38,
                font=Theme.font_body(),
                fg_color=Theme.SURFACE_INPUT,
                border_color=Theme.BORDER,
                corner_radius=8,
            )
            self.sender_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
            ctk.CTkButton(s_row, text="Verify Sender", width=120, height=38, font=Theme.font_body_bold(), fg_color=Theme.ACCENT_BLUE, corner_radius=8, command=self._verify_sender).pack(side="right")

        self.sender_info_lbl = ctk.CTkLabel(card, text="", font=Theme.font_small(), text_color=Theme.ACCENT_CYAN, anchor="w")
        self.sender_info_lbl.pack(fill="x", padx=20, pady=(2, 6))

        # 2. Beneficiary / Receiver Account
        recv_box = ctk.CTkFrame(card, fg_color="transparent")
        recv_box.pack(fill="x", padx=20, pady=4)

        ctk.CTkLabel(recv_box, text="Beneficiary / Receiver Account *", font=Theme.font_small(), text_color=Theme.TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(0, 2))

        r_row = ctk.CTkFrame(recv_box, fg_color="transparent")
        r_row.pack(fill="x")

        self.receiver_entry = ctk.CTkEntry(
            r_row,
            placeholder_text="Enter receiver account number (e.g. 1003928172)",
            height=38,
            font=Theme.font_body(),
            fg_color=Theme.SURFACE_INPUT,
            border_color=Theme.BORDER,
            corner_radius=8,
        )
        self.receiver_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(r_row, text="Verify Beneficiary", width=120, height=38, font=Theme.font_body_bold(), fg_color=Theme.ACCENT_BLUE, corner_radius=8, command=self._verify_receiver).pack(side="right")

        self.receiver_info_lbl = ctk.CTkLabel(card, text="", font=Theme.font_small(), text_color=Theme.ACCENT_CYAN, anchor="w")
        self.receiver_info_lbl.pack(fill="x", padx=20, pady=(2, 8))

        # 3. Transfer Amount & Description
        details_box = ctk.CTkFrame(card, fg_color="transparent")
        details_box.pack(fill="x", padx=20, pady=4)

        ctk.CTkLabel(details_box, text="Transfer Amount ($) *", font=Theme.font_small(), text_color=Theme.TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(0, 2))
        self.amount_entry = ctk.CTkEntry(
            details_box,
            placeholder_text="0.00",
            height=38,
            font=Theme.font_body(),
            fg_color=Theme.SURFACE_INPUT,
            border_color=Theme.BORDER,
            corner_radius=8,
        )
        self.amount_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(details_box, text="Transfer Purpose / Reference Note", font=Theme.font_small(), text_color=Theme.TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(0, 2))
        self.desc_entry = ctk.CTkEntry(
            details_box,
            placeholder_text="e.g. Invoice payment, Family support",
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
            text="Review & Confirm Transfer",
            height=42,
            font=Theme.font_body_bold(),
            fg_color=Theme.ACCENT_BLUE,
            hover_color=Theme.ACCENT_CYAN_HOVER,
            corner_radius=8,
            command=self._confirm_transfer,
        )
        self.submit_btn.pack(fill="x", padx=20, pady=(4, 20))

    def _on_customer_sender_select(self, val: str):
        acct_no = val.split(" - ")[0].strip()
        self.sender_account = account_service.get_by_number(acct_no)

    def _verify_sender(self):
        if not self.sender_entry:
            return
        acct_no = self.sender_entry.get().strip()
        acct = account_service.get_by_number(acct_no)
        if acct:
            self.sender_account = acct
            avail = max(Decimal("0.00"), acct.current_balance - acct.account_type.minimum_balance)
            self.sender_info_lbl.configure(
                text=f"✓ Verified: {acct.customer.full_name}  •  Available: {format_currency(avail)}",
                text_color=Theme.SUCCESS,
            )
        else:
            self.sender_account = None
            self.sender_info_lbl.configure(text="Sender account not found.", text_color=Theme.DANGER)

    def _verify_receiver(self):
        acct_no = self.receiver_entry.get().strip()
        acct = account_service.get_by_number(acct_no)
        if acct:
            self.receiver_account = acct
            self.receiver_info_lbl.configure(
                text=f"✓ Beneficiary: {acct.customer.full_name} ({acct.account_type.name})",
                text_color=Theme.SUCCESS,
            )
        else:
            self.receiver_account = None
            self.receiver_info_lbl.configure(text="Beneficiary account not found.", text_color=Theme.DANGER)

    def _confirm_transfer(self):
        self.status_lbl.configure(text="")
        if self.sender_entry and not self.sender_account:
            self._verify_sender()
        if not self.receiver_account:
            self._verify_receiver()

        if not self.sender_account or not self.receiver_account:
            self.status_lbl.configure(text="Please verify both sender and receiver accounts.")
            return

        if self.sender_account.account_number == self.receiver_account.account_number:
            self.status_lbl.configure(text="Sender and receiver accounts cannot be the same.")
            return

        amt_str = self.amount_entry.get().strip()
        try:
            amt = Decimal(amt_str.replace(",", ""))
            if amt <= 0:
                self.status_lbl.configure(text="Amount must be positive.")
                return
        except Exception:
            self.status_lbl.configure(text="Please enter a valid amount.")
            return

        desc = self.desc_entry.get().strip() or "Internal Transfer"

        ConfirmModal(
            self,
            title="Confirm Fund Transfer",
            message=(
                f"Transfer ${amt:,.2f} from {self.sender_account.account_number} ({self.sender_account.customer.full_name})\n"
                f"to {self.receiver_account.account_number} ({self.receiver_account.customer.full_name})?"
            ),
            confirm_label="Send Funds Now",
            on_confirm=lambda: self._execute_transfer(amt_str, desc),
        )

    def _execute_transfer(self, amt_str: str, desc: str):
        ok, receipt, msg = transaction_service.transfer(
            sender_account_no=self.sender_account.account_number,
            receiver_account_no=self.receiver_account.account_number,
            amount_input=amt_str,
            description=desc,
            user_id=self.current_session.user_id,
        )

        if ok and receipt:
            self.amount_entry.delete(0, "end")
            self.desc_entry.delete(0, "end")
            self._verify_sender()
            ReceiptModal(self, receipt)
        else:
            self.status_lbl.configure(text=msg)

