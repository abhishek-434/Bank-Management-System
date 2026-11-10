"""Educational loan management, approval, and repayment interface."""
from decimal import Decimal
from tkinter import messagebox
import customtkinter as ctk
from ui.theme import Theme
from ui.components.data_table import DataTable
from ui.components.modal import ConfirmModal
from services.loan_service import loan_service
from services.customer_service import customer_service
from services.account_service import account_service
from services.auth_service import SessionContext
from utils.formatters import format_currency


class LoanMgmtView(ctk.CTkFrame):
    """Educational demonstration loan interface supporting applications, reviews, and repayments."""

    def __init__(self, master, current_session: SessionContext, **kwargs):
        super().__init__(master, fg_color=Theme.BG_DARK, **kwargs)

        self.current_session = current_session
        self.status_filter = "ALL"

        self._build_ui()
        self.refresh_loans()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(16, 8))

        title_lbl = ctk.CTkLabel(
            header,
            text="Loan Operations & Repayments",
            font=Theme.font_title(),
            text_color=Theme.TEXT_PRIMARY,
        )
        title_lbl.pack(side="left")

        apply_btn = ctk.CTkButton(
            header,
            text="+ Apply for Loan",
            height=36,
            font=Theme.font_body_bold(),
            fg_color=Theme.ACCENT_BLUE,
            hover_color=Theme.ACCENT_CYAN_HOVER,
            corner_radius=8,
            command=self._open_apply_modal,
        )
        apply_btn.pack(side="right")

        # Disclaimer banner
        banner = ctk.CTkFrame(self, fg_color=Theme.SURFACE_CARD, corner_radius=8)
        banner.pack(fill="x", padx=24, pady=(0, 12))

        ctk.CTkLabel(
            banner,
            text="ℹ Educational Simulation Model: Simplified simple-interest calculations used for demonstration purposes only.",
            font=Theme.font_small(),
            text_color=Theme.ACCENT_CYAN,
        ).pack(padx=16, pady=8)

        # Table
        table_container = ctk.CTkFrame(self, fg_color="transparent")
        table_container.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        columns = ["Loan Ref", "Borrower", "Principal", "Rate", "Tenure", "Total Due", "Outstanding", "Status"]
        col_widths = [130, 140, 100, 70, 70, 100, 110, 90]

        self.table = DataTable(
            table_container,
            columns=columns,
            col_widths=col_widths,
            search_placeholder="Search by loan reference or customer...",
            on_search=self._on_search,
            on_row_click=self._on_row_click,
        )
        self.table.pack(fill="both", expand=True)

    def refresh_loans(self, query: str = ""):
        cust_id = self.current_session.customer_id if self.current_session.is_customer else None
        loans = loan_service.list_loans(customer_id=cust_id, status_filter=self.status_filter)

        rows = []
        for ln in loans:
            if query:
                q = query.lower()
                matches = (
                    q in ln.loan_reference.lower()
                    or (ln.customer and q in ln.customer.full_name.lower())
                )
                if not matches:
                    continue

            rows.append({
                "raw_loan": ln,
                "id": ln.id,
                "Loan Ref": ln.loan_reference,
                "Borrower": ln.customer.full_name if ln.customer else "N/A",
                "Principal": format_currency(ln.principal_amount),
                "Rate": f"{ln.interest_rate}%",
                "Tenure": f"{ln.duration_months} mo",
                "Total Due": format_currency(ln.total_payable),
                "Outstanding": format_currency(ln.outstanding_balance),
                "Status": ln.status,
                "status": ln.status,
            })

        self.table.set_data(
            rows,
            key_fields=["Loan Ref", "Borrower", "Principal", "Rate", "Tenure", "Total Due", "Outstanding", "Status"],
        )

    def _on_search(self, query: str):
        self.refresh_loans(query)

    def _on_row_click(self, row_data):
        ln = row_data.get("raw_loan")
        if ln:
            self._open_loan_detail_modal(ln.id)

    def _open_apply_modal(self):
        """Modal for submitting a loan application with live interest computation."""
        modal = ctk.CTkToplevel(self)
        modal.title("Apply for Loan - Apex Horizon Bank")
        modal.geometry("520x620")
        modal.resizable(False, False)
        modal.configure(fg_color=Theme.BG_DARK)
        modal.transient(self)
        modal.grab_set()

        container = ctk.CTkFrame(modal, fg_color=Theme.SURFACE_CARD, corner_radius=12)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text="Loan Application", font=Theme.font_subtitle(), text_color=Theme.TEXT_PRIMARY).pack(pady=(16, 8))

        form = ctk.CTkFrame(container, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20)

        # 1. Customer
        if self.current_session.is_customer and self.current_session.customer_id:
            cust = customer_service.get_by_id(self.current_session.customer_id)
            cust_id = cust.id
            ctk.CTkLabel(form, text=f"Applicant: {cust.full_name} ({cust.customer_code})", font=Theme.font_body_bold(), text_color=Theme.TEXT_PRIMARY).pack(fill="x", pady=6)
            cust_dropdown = None
        else:
            customers = customer_service.search_customers(status_filter="ACTIVE")
            cust_map = {f"{c.customer_code} - {c.full_name}": c.id for c in customers}
            cust_opts = list(cust_map.keys()) or ["No active customers"]

            ctk.CTkLabel(form, text="Select Applicant Customer *", font=Theme.font_small(), text_color=Theme.TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(4, 2))
            cust_dropdown = ctk.CTkOptionMenu(
                form,
                values=cust_opts,
                height=36,
                font=Theme.font_body(),
                fg_color=Theme.SURFACE_INPUT,
                button_color=Theme.ACCENT_BLUE,
                corner_radius=8,
            )
            cust_dropdown.pack(fill="x", pady=(0, 8))

        # 2. Principal Amount
        ctk.CTkLabel(form, text="Loan Principal Amount ($) *", font=Theme.font_small(), text_color=Theme.TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(4, 2))
        principal_entry = ctk.CTkEntry(
            form,
            placeholder_text="e.g. 10000.00",
            height=36,
            font=Theme.font_body(),
            fg_color=Theme.SURFACE_INPUT,
            border_color=Theme.BORDER,
            corner_radius=8,
        )
        principal_entry.pack(fill="x", pady=(0, 8))
        principal_entry.insert(0, "10000.00")

        # 3. Interest Rate
        ctk.CTkLabel(form, text="Annual Interest Rate (%) *", font=Theme.font_small(), text_color=Theme.TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(4, 2))
        rate_entry = ctk.CTkEntry(
            form,
            placeholder_text="e.g. 6.50",
            height=36,
            font=Theme.font_body(),
            fg_color=Theme.SURFACE_INPUT,
            border_color=Theme.BORDER,
            corner_radius=8,
        )
        rate_entry.pack(fill="x", pady=(0, 8))
        rate_entry.insert(0, "6.50")

        # 4. Duration
        ctk.CTkLabel(form, text="Loan Tenure (Months) *", font=Theme.font_small(), text_color=Theme.TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(4, 2))
        duration_entry = ctk.CTkEntry(
            form,
            placeholder_text="e.g. 24",
            height=36,
            font=Theme.font_body(),
            fg_color=Theme.SURFACE_INPUT,
            border_color=Theme.BORDER,
            corner_radius=8,
        )
        duration_entry.pack(fill="x", pady=(0, 10))
        duration_entry.insert(0, "24")

        # Live Calculation Preview
        preview_box = ctk.CTkFrame(form, fg_color=Theme.SURFACE_NAV, corner_radius=8)
        preview_box.pack(fill="x", pady=4)

        calc_lbl = ctk.CTkLabel(
            preview_box,
            text="Estimated Total Due: $11,300.00 • Est. Monthly: $470.83",
            font=Theme.font_small(),
            text_color=Theme.ACCENT_CYAN,
        )
        calc_lbl.pack(padx=12, pady=10)

        def update_calc(*args):
            try:
                p = Decimal(principal_entry.get().strip().replace(",", ""))
                r = Decimal(rate_entry.get().strip())
                m = int(duration_entry.get().strip())
                interest, total = loan_service.calculate_loan_totals(p, r, m)
                emi = total / Decimal(m)
                calc_lbl.configure(text=f"Total Interest: ${interest:,.2f} • Total Due: ${total:,.2f} • Monthly EMI: ${emi:,.2f}")
            except Exception:
                calc_lbl.configure(text="Enter valid numerical inputs to calculate estimate.")

        principal_entry.bind("<KeyRelease>", update_calc)
        rate_entry.bind("<KeyRelease>", update_calc)
        duration_entry.bind("<KeyRelease>", update_calc)

        err_lbl = ctk.CTkLabel(form, text="", font=Theme.font_small(), text_color=Theme.DANGER)
        err_lbl.pack(pady=4)

        def submit():
            err_lbl.configure(text="")
            c_id = cust_id if cust_dropdown is None else cust_map.get(cust_dropdown.get())
            if not c_id:
                err_lbl.configure(text="Please select a valid customer.")
                return

            try:
                p = Decimal(principal_entry.get().strip().replace(",", ""))
                r = Decimal(rate_entry.get().strip())
                m = int(duration_entry.get().strip())
            except Exception:
                err_lbl.configure(text="Invalid numeric inputs.")
                return

            ok, ln, msg = loan_service.apply_for_loan(
                customer_id=c_id,
                principal_input=p,
                annual_rate=r,
                duration_months=m,
                applied_by_user_id=self.current_session.user_id,
            )
            if ok:
                messagebox.showinfo("Application Submitted", msg)
                modal.destroy()
                self.refresh_loans()
            else:
                err_lbl.configure(text=msg)

        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=16)

        ctk.CTkButton(btn_row, text="Submit Application", height=38, fg_color=Theme.SUCCESS, hover_color=Theme.SUCCESS_HOVER, font=Theme.font_body_bold(), corner_radius=8, command=submit).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(btn_row, text="Cancel", height=38, fg_color="transparent", border_color=Theme.BORDER, border_width=1, font=Theme.font_body(), corner_radius=8, command=modal.destroy).pack(side="right", fill="x", expand=True, padx=(6, 0))

    def _open_loan_detail_modal(self, loan_id: str):
        """View loan repayments, approval options, or process repayments."""
        loans = loan_service.list_loans()
        target = next((l for l in loans if l.id == loan_id), None)
        if not target:
            return

        modal = ctk.CTkToplevel(self)
        modal.title(f"Loan Details - {target.loan_reference}")
        modal.geometry("540x620")
        modal.resizable(False, False)
        modal.configure(fg_color=Theme.BG_DARK)
        modal.transient(self)
        modal.grab_set()

        container = ctk.CTkFrame(modal, fg_color=Theme.SURFACE_CARD, corner_radius=12)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text=f"Loan {target.loan_reference}", font=Theme.font_subtitle(), text_color=Theme.TEXT_PRIMARY).pack(pady=(16, 2))
        ctk.CTkLabel(container, text=f"Borrower: {target.customer.full_name} • Status: {target.status}", font=Theme.font_small(), text_color=Theme.ACCENT_CYAN).pack(pady=(0, 10))

        # Financial breakdown card
        box = ctk.CTkFrame(container, fg_color=Theme.SURFACE_NAV, corner_radius=8)
        box.pack(fill="x", padx=16, pady=6)

        fields = [
            ("Principal Amount", format_currency(target.principal_amount)),
            ("Interest Rate", f"{target.interest_rate}% p.a."),
            ("Tenure Duration", f"{target.duration_months} Months"),
            ("Total Payable Amount", format_currency(target.total_payable)),
            ("Remaining Balance", format_currency(target.outstanding_balance)),
            ("Applied Date", target.applied_at.strftime("%Y-%m-%d")),
        ]
        for k, v in fields:
            r = ctk.CTkFrame(box, fg_color="transparent")
            r.pack(fill="x", padx=12, pady=3)
            ctk.CTkLabel(r, text=k, width=150, font=Theme.font_small(), text_color=Theme.TEXT_SECONDARY, anchor="w").pack(side="left")
            ctk.CTkLabel(r, text=str(v), font=Theme.font_body_bold(), text_color=Theme.TEXT_PRIMARY, anchor="w").pack(side="left")

        # Repayments Table
        ctk.CTkLabel(container, text="RECORDED REPAYMENTS", font=Theme.font_section(), text_color=Theme.TEXT_SECONDARY, anchor="w").pack(fill="x", padx=16, pady=(10, 4))
        rep_box = ctk.CTkScrollableFrame(container, height=110, fg_color=Theme.SURFACE_NAV, corner_radius=8)
        rep_box.pack(fill="x", padx=16, pady=4)

        if target.repayments:
            for rep in target.repayments:
                r_row = ctk.CTkFrame(rep_box, fg_color="transparent")
                r_row.pack(fill="x", pady=2)
                ctk.CTkLabel(r_row, text=f"{rep.payment_reference} ({rep.paid_at.strftime('%Y-%m-%d')})", font=Theme.font_small(), text_color=Theme.TEXT_PRIMARY).pack(side="left")
                ctk.CTkLabel(r_row, text=f"${rep.amount:,.2f}", font=Theme.font_body_bold(), text_color=Theme.SUCCESS).pack(side="right")
        else:
            ctk.CTkLabel(rep_box, text="No repayments recorded yet.", font=Theme.font_small(), text_color=Theme.TEXT_MUTED).pack(pady=10)

        # Action Buttons
        btn_box = ctk.CTkFrame(container, fg_color="transparent")
        btn_box.pack(fill="x", padx=16, pady=16)

        # 1. Approval / Rejection (Staff/Admin only on APPLIED status)
        if not self.current_session.is_customer and target.status == "APPLIED":
            def approve_loan():
                # Disburse to first active customer account if exists
                accts = account_service.list_by_customer(target.customer_id)
                disburse_acct = accts[0].account_number if accts else None
                ok, msg = loan_service.review_loan(
                    loan_id=target.id,
                    approve=True,
                    reviewed_by_user_id=self.current_session.user_id,
                    disburse_account_number=disburse_acct,
                )
                if ok:
                    messagebox.showinfo("Loan Approved", msg)
                    modal.destroy()
                    self.refresh_loans()
                else:
                    messagebox.showerror("Error", msg)

            def reject_loan():
                ok, msg = loan_service.review_loan(
                    loan_id=target.id,
                    approve=False,
                    reviewed_by_user_id=self.current_session.user_id,
                )
                if ok:
                    messagebox.showinfo("Loan Rejected", msg)
                    modal.destroy()
                    self.refresh_loans()
                else:
                    messagebox.showerror("Error", msg)

            ctk.CTkButton(btn_box, text="Approve & Disburse", fg_color=Theme.SUCCESS, hover_color=Theme.SUCCESS_HOVER, corner_radius=8, command=approve_loan).pack(side="left", fill="x", expand=True, padx=(0, 4))
            ctk.CTkButton(btn_box, text="Reject", fg_color=Theme.DANGER, hover_color=Theme.DANGER_HOVER, corner_radius=8, command=reject_loan).pack(side="right", fill="x", expand=True, padx=(4, 0))

        # 2. Make Repayment (if active balance)
        elif target.status in ("APPROVED", "DISBURSED") and target.outstanding_balance > Decimal("0.00"):
            def open_repayment():
                modal.destroy()
                self._open_make_repayment_modal(target)

            ctk.CTkButton(btn_box, text="Make Repayment", fg_color=Theme.ACCENT_BLUE, hover_color=Theme.ACCENT_CYAN_HOVER, corner_radius=8, command=open_repayment).pack(fill="x")

    def _open_make_repayment_modal(self, loan):
        """Dialog to submit a repayment."""
        modal = ctk.CTkToplevel(self)
        modal.title(f"Loan Repayment - {loan.loan_reference}")
        modal.geometry("460x360")
        modal.resizable(False, False)
        modal.configure(fg_color=Theme.BG_DARK)
        modal.transient(self)
        modal.grab_set()

        container = ctk.CTkFrame(modal, fg_color=Theme.SURFACE_CARD, corner_radius=12)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text="Submit Repayment", font=Theme.font_subtitle(), text_color=Theme.TEXT_PRIMARY).pack(pady=(16, 4))
        ctk.CTkLabel(container, text=f"Outstanding: {format_currency(loan.outstanding_balance)}", font=Theme.font_body_bold(), text_color=Theme.ACCENT_CYAN).pack(pady=(0, 14))

        ctk.CTkLabel(container, text="Repayment Amount ($) *", font=Theme.font_small(), text_color=Theme.TEXT_SECONDARY, anchor="w").pack(fill="x", padx=20, pady=(4, 2))
        amt_entry = ctk.CTkEntry(container, height=38, font=Theme.font_body(), fg_color=Theme.SURFACE_INPUT, border_color=Theme.BORDER, corner_radius=8)
        amt_entry.pack(fill="x", padx=20, pady=(0, 10))
        amt_entry.insert(0, str(min(Decimal("500.00"), loan.outstanding_balance)))

        err_lbl = ctk.CTkLabel(container, text="", font=Theme.font_small(), text_color=Theme.DANGER)
        err_lbl.pack(pady=4)

        def do_repay():
            try:
                amt = Decimal(amt_entry.get().strip().replace(",", ""))
            except Exception:
                err_lbl.configure(text="Invalid repayment amount.")
                return

            ok, msg = loan_service.repay_loan(
                loan_id=loan.id,
                repayment_amount_input=amt,
                user_id=self.current_session.user_id,
            )
            if ok:
                messagebox.showinfo("Repayment Processed", msg)
                modal.destroy()
                self.refresh_loans()
            else:
                err_lbl.configure(text=msg)

        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=16)

        ctk.CTkButton(btn_row, text="Confirm Payment", height=38, fg_color=Theme.SUCCESS, hover_color=Theme.SUCCESS_HOVER, font=Theme.font_body_bold(), corner_radius=8, command=do_repay).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(btn_row, text="Cancel", height=38, fg_color="transparent", border_color=Theme.BORDER, border_width=1, font=Theme.font_body(), corner_radius=8, command=modal.destroy).pack(side="right", fill="x", expand=True, padx=(6, 0))

