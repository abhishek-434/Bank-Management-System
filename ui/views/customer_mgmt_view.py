"""Customer profile and management CRUD view."""
from datetime import date, datetime
from tkinter import messagebox
from typing import Optional
import customtkinter as ctk
from ui.theme import Theme
from ui.components.data_table import DataTable
from ui.components.modal import ConfirmModal
from services.customer_service import customer_service
from services.auth_service import SessionContext


class CustomerMgmtView(ctk.CTkFrame):
    """Customer CRUD interface with search, registration modal, and profile viewer."""

    def __init__(self, master, current_session: SessionContext, **kwargs):
        super().__init__(master, fg_color=Theme.BG_DARK, **kwargs)

        self.current_session = current_session
        self._build_ui()
        self.refresh_customers()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(16, 12))

        title_lbl = ctk.CTkLabel(
            header,
            text="Customer Management",
            font=Theme.font_title(),
            text_color=Theme.TEXT_PRIMARY,
        )
        title_lbl.pack(side="left")

        reg_btn = ctk.CTkButton(
            header,
            text="+ Register Customer",
            height=36,
            font=Theme.font_body_bold(),
            fg_color=Theme.ACCENT_BLUE,
            hover_color=Theme.ACCENT_CYAN_HOVER,
            corner_radius=8,
            command=self._open_register_modal,
        )
        reg_btn.pack(side="right")

        # Table
        table_container = ctk.CTkFrame(self, fg_color="transparent")
        table_container.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        columns = ["Customer Code", "Full Name", "Email Address", "Phone", "Accounts", "Status", "Registered"]
        col_widths = [120, 140, 160, 110, 80, 90, 100]

        self.table = DataTable(
            table_container,
            columns=columns,
            col_widths=col_widths,
            search_placeholder="Search by name, customer code, or email...",
            on_search=self._on_search,
            on_row_click=self._on_row_click,
        )
        self.table.pack(fill="both", expand=True)

    def refresh_customers(self, query: str = ""):
        customers = customer_service.search_customers(search_query=query)
        rows = [
            {
                "id": c.id,
                "Customer Code": c.customer_code,
                "Full Name": c.full_name,
                "Email Address": c.email,
                "Phone": c.phone,
                "Accounts": len(c.accounts),
                "Status": c.status,
                "status": c.status,
                "Registered": c.created_at.strftime("%Y-%m-%d") if c.created_at else "",
            }
            for c in customers
        ]
        self.table.set_data(
            rows,
            key_fields=["Customer Code", "Full Name", "Email Address", "Phone", "Accounts", "Status", "Registered"],
        )

    def _on_search(self, query: str):
        self.refresh_customers(query)

    def _on_row_click(self, row_data):
        cust_id = row_data.get("id")
        if cust_id:
            self._open_profile_modal(cust_id)

    def _open_register_modal(self):
        """Modal for onboarding a new customer."""
        modal = ctk.CTkToplevel(self)
        modal.title("Register New Customer - Apex Horizon Bank")
        modal.geometry("540x660")
        modal.resizable(False, False)
        modal.configure(fg_color=Theme.BG_DARK)
        modal.transient(self)
        modal.grab_set()

        container = ctk.CTkFrame(modal, fg_color=Theme.SURFACE_CARD, corner_radius=12)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text="New Customer Registration", font=Theme.font_subtitle(), text_color=Theme.TEXT_PRIMARY).pack(pady=(16, 12))

        form = ctk.CTkScrollableFrame(container, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        def make_entry(lbl_text, default=""):
            ctk.CTkLabel(form, text=lbl_text, font=Theme.font_small(), text_color=Theme.TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(4, 2))
            ent = ctk.CTkEntry(form, height=36, font=Theme.font_body(), fg_color=Theme.SURFACE_INPUT, border_color=Theme.BORDER, corner_radius=8)
            ent.pack(fill="x", pady=(0, 6))
            if default:
                ent.insert(0, default)
            return ent

        e_fn = make_entry("First Name *")
        e_ln = make_entry("Last Name *")
        e_dob = make_entry("Date of Birth (YYYY-MM-DD) *", "1990-01-15")
        e_email = make_entry("Email Address *")
        e_phone = make_entry("Phone Number *", "+1-555-")
        e_addr = make_entry("Residential Address *")
        e_gid = make_entry("Govt ID Reference (e.g. DL-12345) *")
        e_user = make_entry("Online Portal Username (Optional)")
        e_pwd = make_entry("Online Portal Password (Optional)")

        err_lbl = ctk.CTkLabel(container, text="", font=Theme.font_small(), text_color=Theme.DANGER)
        err_lbl.pack(pady=4)

        def save():
            err_lbl.configure(text="")
            try:
                dob = datetime.strptime(e_dob.get().strip(), "%Y-%m-%d").date()
            except ValueError:
                err_lbl.configure(text="Invalid Date of Birth format. Please use YYYY-MM-DD.")
                return

            success, cust, msg = customer_service.register_customer(
                first_name=e_fn.get(),
                last_name=e_ln.get(),
                date_of_birth=dob,
                email=e_email.get(),
                phone=e_phone.get(),
                address=e_addr.get(),
                govt_id=e_gid.get(),
                username=e_user.get().strip() or None,
                password=e_pwd.get().strip() or None,
                created_by_user_id=self.current_session.user_id,
            )
            if success:
                messagebox.showinfo("Success", f"Customer {cust.full_name} ({cust.customer_code}) registered successfully!")
                modal.destroy()
                self.refresh_customers()
            else:
                err_lbl.configure(text=msg)

        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=12)

        ctk.CTkButton(btn_row, text="Create Customer", height=38, fg_color=Theme.SUCCESS, hover_color=Theme.SUCCESS_HOVER, font=Theme.font_body_bold(), corner_radius=8, command=save).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(btn_row, text="Cancel", height=38, fg_color="transparent", border_color=Theme.BORDER, border_width=1, font=Theme.font_body(), corner_radius=8, command=modal.destroy).pack(side="right", fill="x", expand=True, padx=(6, 0))

    def _open_profile_modal(self, customer_id: str):
        """View and update customer profile details and linked accounts."""
        cust = customer_service.get_by_id(customer_id)
        if not cust:
            return

        modal = ctk.CTkToplevel(self)
        modal.title(f"Customer Profile - {cust.full_name}")
        modal.geometry("560x650")
        modal.resizable(False, False)
        modal.configure(fg_color=Theme.BG_DARK)
        modal.transient(self)
        modal.grab_set()

        container = ctk.CTkFrame(modal, fg_color=Theme.SURFACE_CARD, corner_radius=12)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header info
        ctk.CTkLabel(container, text=cust.full_name, font=Theme.font_subtitle(), text_color=Theme.TEXT_PRIMARY).pack(pady=(16, 2))
        ctk.CTkLabel(container, text=f"Customer ID: {cust.customer_code} • Status: {cust.status}", font=Theme.font_small(), text_color=Theme.ACCENT_CYAN).pack(pady=(0, 12))

        # Editable fields
        edit_box = ctk.CTkFrame(container, fg_color=Theme.SURFACE_NAV, corner_radius=8)
        edit_box.pack(fill="x", padx=16, pady=6)

        def make_row(parent, label, val):
            r = ctk.CTkFrame(parent, fg_color="transparent")
            r.pack(fill="x", padx=12, pady=4)
            ctk.CTkLabel(r, text=label, width=120, font=Theme.font_small(), text_color=Theme.TEXT_SECONDARY, anchor="w").pack(side="left")
            ent = ctk.CTkEntry(r, height=32, font=Theme.font_body(), fg_color=Theme.SURFACE_INPUT, border_color=Theme.BORDER, corner_radius=6)
            ent.pack(side="left", fill="x", expand=True)
            ent.insert(0, val)
            return ent

        e_fn = make_row(edit_box, "First Name", cust.first_name)
        e_ln = make_row(edit_box, "Last Name", cust.last_name)
        e_phone = make_row(edit_box, "Phone", cust.phone)
        e_addr = make_row(edit_box, "Address", cust.address)

        # Linked Accounts section
        ctk.CTkLabel(container, text="LINKED BANK ACCOUNTS", font=Theme.font_section(), text_color=Theme.TEXT_SECONDARY, anchor="w").pack(fill="x", padx=16, pady=(12, 4))
        accts_box = ctk.CTkScrollableFrame(container, height=110, fg_color=Theme.SURFACE_NAV, corner_radius=8)
        accts_box.pack(fill="x", padx=16, pady=4)

        if cust.accounts:
            for acct in cust.accounts:
                arow = ctk.CTkFrame(accts_box, fg_color="transparent")
                arow.pack(fill="x", pady=2)
                ctk.CTkLabel(arow, text=f"{acct.account_number} ({acct.account_type.code if acct.account_type else 'ACC'})", font=Theme.font_body_bold(), text_color=Theme.TEXT_PRIMARY).pack(side="left")
                ctk.CTkLabel(arow, text=f"${acct.current_balance:,.2f}", font=Theme.font_body_bold(), text_color=Theme.SUCCESS).pack(side="right")
        else:
            ctk.CTkLabel(accts_box, text="No bank accounts opened yet.", font=Theme.font_small(), text_color=Theme.TEXT_MUTED).pack(pady=10)

        # Action Buttons (Status toggle and Save)
        action_row = ctk.CTkFrame(container, fg_color="transparent")
        action_row.pack(fill="x", padx=16, pady=(14, 8))

        def save_changes():
            ok, msg = customer_service.update_customer(
                customer_id=cust.id,
                first_name=e_fn.get(),
                last_name=e_ln.get(),
                phone=e_phone.get(),
                address=e_addr.get(),
                updated_by_user_id=self.current_session.user_id,
            )
            if ok:
                messagebox.showinfo("Success", "Customer profile updated!")
                modal.destroy()
                self.refresh_customers()
            else:
                messagebox.showerror("Error", msg)

        def toggle_status():
            new_st = "INACTIVE" if cust.status == "ACTIVE" else "ACTIVE"
            ok, msg = customer_service.set_status(cust.id, new_st, self.current_session.user_id)
            if ok:
                messagebox.showinfo("Updated", msg)
                modal.destroy()
                self.refresh_customers()
            else:
                messagebox.showerror("Error", msg)

        ctk.CTkButton(action_row, text="Save Updates", fg_color=Theme.ACCENT_BLUE, hover_color=Theme.ACCENT_CYAN_HOVER, corner_radius=8, command=save_changes).pack(side="left", fill="x", expand=True, padx=(0, 4))
        st_color = Theme.DANGER if cust.status == "ACTIVE" else Theme.SUCCESS
        st_txt = "Deactivate Customer" if cust.status == "ACTIVE" else "Activate Customer"
        ctk.CTkButton(action_row, text=st_txt, fg_color=st_color, corner_radius=8, command=toggle_status).pack(side="left", fill="x", expand=True, padx=4)
        ctk.CTkButton(action_row, text="Close", fg_color="transparent", border_color=Theme.BORDER, border_width=1, corner_radius=8, command=modal.destroy).pack(side="right", padx=(4, 0))

