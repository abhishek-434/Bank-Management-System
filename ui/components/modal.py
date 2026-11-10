"""Modal dialogs for receipts, user confirmations, and error alerts."""
import os
from datetime import datetime
from tkinter import filedialog, messagebox
from typing import Dict, Any, Callable, Optional
import customtkinter as ctk
from ui.theme import Theme
from utils.formatters import format_currency, format_datetime
from services.pdf_service import pdf_service
from config.settings import settings


class ReceiptModal(ctk.CTkToplevel):
    """Invoice-style receipt dialog with PDF export button."""

    def __init__(self, master, receipt: Dict[str, Any]):
        super().__init__(master)

        self.receipt = receipt
        self.title("Transaction Receipt - Apex Horizon Bank")
        self.geometry("520x640")
        self.resizable(False, False)
        self.configure(fg_color=Theme.BG_DARK)

        # Center on parent
        self.transient(master)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(
            self,
            fg_color=Theme.SURFACE_CARD,
            border_color=Theme.BORDER,
            border_width=1,
            corner_radius=12,
        )
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        brand_lbl = ctk.CTkLabel(
            container,
            text="APEX HORIZON BANK",
            font=Theme.font_subtitle(),
            text_color=Theme.ACCENT_CYAN,
        )
        brand_lbl.pack(pady=(16, 2))

        sub_lbl = ctk.CTkLabel(
            container,
            text="Official Electronic Transaction Receipt",
            font=Theme.font_small(),
            text_color=Theme.TEXT_MUTED,
        )
        sub_lbl.pack(pady=(0, 12))

        sep1 = ctk.CTkFrame(container, height=1, fg_color=Theme.BORDER)
        sep1.pack(fill="x", padx=16, pady=(0, 16))

        # Amount Highlight
        amt = self.receipt.get("amount", 0)
        amt_lbl = ctk.CTkLabel(
            container,
            text=format_currency(amt),
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=28, weight="bold"),
            text_color=Theme.SUCCESS,
        )
        amt_lbl.pack(pady=4)

        status_lbl = ctk.CTkLabel(
            container,
            text=f"● {self.receipt.get('status', 'SUCCESS')}",
            font=Theme.font_body_bold(),
            text_color=Theme.SUCCESS,
        )
        status_lbl.pack(pady=(0, 16))

        # Details list
        details_frame = ctk.CTkFrame(container, fg_color=Theme.SURFACE_NAV, corner_radius=8)
        details_frame.pack(fill="both", expand=True, padx=16, pady=4)

        fields = [
            ("Receipt Type", self.receipt.get("receipt_type", "TRANSACTION")),
            ("Reference", self.receipt.get("reference_no") or self.receipt.get("transfer_reference", "N/A")),
            ("Date & Time", format_datetime(self.receipt.get("timestamp"))),
            ("Account No", self.receipt.get("account_number") or self.receipt.get("sender_account", "N/A")),
            ("Account Holder", self.receipt.get("customer_name") or self.receipt.get("sender_name", "N/A")),
        ]

        if "receiver_account" in self.receipt:
            fields.append(("Beneficiary", f"{self.receipt['receiver_account']} ({self.receipt.get('receiver_name', '')})"))
        if "new_balance" in self.receipt:
            fields.append(("New Balance", format_currency(self.receipt["new_balance"])))
        if "description" in self.receipt:
            fields.append(("Description", self.receipt["description"]))

        for r_idx, (k, v) in enumerate(fields):
            row = ctk.CTkFrame(details_frame, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=6)

            k_lbl = ctk.CTkLabel(row, text=k, font=Theme.font_small(), text_color=Theme.TEXT_SECONDARY, width=110, anchor="w")
            k_lbl.pack(side="left")

            v_lbl = ctk.CTkLabel(row, text=str(v), font=Theme.font_body_bold(), text_color=Theme.TEXT_PRIMARY, anchor="w")
            v_lbl.pack(side="left", fill="x", expand=True)

        # Buttons
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=16)

        pdf_btn = ctk.CTkButton(
            btn_frame,
            text="Download PDF Receipt",
            height=36,
            fg_color=Theme.ACCENT_BLUE,
            hover_color=Theme.ACCENT_CYAN_HOVER,
            font=Theme.font_body_bold(),
            corner_radius=8,
            command=self._export_pdf,
        )
        pdf_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        close_btn = ctk.CTkButton(
            btn_frame,
            text="Done",
            width=80,
            height=36,
            fg_color="transparent",
            border_color=Theme.BORDER,
            border_width=1,
            hover_color=Theme.SURFACE_NAV,
            text_color=Theme.TEXT_SECONDARY,
            font=Theme.font_body(),
            corner_radius=8,
            command=self.destroy,
        )
        close_btn.pack(side="right", padx=(6, 0))

    def _export_pdf(self):
        ref = self.receipt.get("reference_no") or self.receipt.get("transfer_reference", "receipt")
        default_name = f"Receipt_{ref}_{datetime.now().strftime('%Y%m%d%H%M')}.pdf"
        dest = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Document", "*.pdf")],
            initialdir=str(settings.RECEIPTS_DIR),
            initialfile=default_name,
        )
        if dest:
            try:
                pdf_service.generate_receipt_pdf(self.receipt, dest)
                messagebox.showinfo("Export Successful", f"Receipt PDF saved successfully to:\n{dest}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Failed to generate receipt PDF:\n{e}")


class ConfirmModal(ctk.CTkToplevel):
    """Reusable confirmation popup."""

    def __init__(
        self,
        master,
        title: str,
        message: str,
        on_confirm: Callable[[], None],
        confirm_label: str = "Confirm",
        is_destructive: bool = False,
    ):
        super().__init__(master)
        self.title(title)
        self.geometry("420x220")
        self.resizable(False, False)
        self.configure(fg_color=Theme.BG_DARK)

        self.on_confirm = on_confirm
        self.transient(master)
        self.grab_set()

        container = ctk.CTkFrame(self, fg_color=Theme.SURFACE_CARD, corner_radius=12)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        t_lbl = ctk.CTkLabel(container, text=title, font=Theme.font_subtitle(), text_color=Theme.TEXT_PRIMARY)
        t_lbl.pack(pady=(16, 8))

        m_lbl = ctk.CTkLabel(container, text=message, font=Theme.font_body(), text_color=Theme.TEXT_SECONDARY, wraplength=360)
        m_lbl.pack(pady=(0, 20), padx=16)

        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 14))

        color = Theme.DANGER if is_destructive else Theme.ACCENT_BLUE
        hover = Theme.DANGER_HOVER if is_destructive else Theme.ACCENT_CYAN_HOVER

        confirm_btn = ctk.CTkButton(
            btn_row,
            text=confirm_label,
            fg_color=color,
            hover_color=hover,
            font=Theme.font_body_bold(),
            corner_radius=8,
            command=self._handle_confirm,
        )
        confirm_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        cancel_btn = ctk.CTkButton(
            btn_row,
            text="Cancel",
            fg_color="transparent",
            border_color=Theme.BORDER,
            border_width=1,
            hover_color=Theme.SURFACE_NAV,
            text_color=Theme.TEXT_SECONDARY,
            font=Theme.font_body(),
            corner_radius=8,
            command=self.destroy,
        )
        cancel_btn.pack(side="right", fill="x", expand=True, padx=(6, 0))

    def _handle_confirm(self):
        self.destroy()
        self.on_confirm()


class AlertModal:
    """Helper for standard notifications."""

    @staticmethod
    def show_info(title: str, msg: str):
        messagebox.showinfo(title, msg)

    @staticmethod
    def show_error(title: str, msg: str):
        messagebox.showerror(title, msg)

    @staticmethod
    def show_warning(title: str, msg: str):
        messagebox.showwarning(title, msg)

