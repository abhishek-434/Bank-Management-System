"""Employee and staff management administration view."""
from tkinter import messagebox
import customtkinter as ctk
from ui.theme import Theme
from ui.components.data_table import DataTable
from services.employee_service import employee_service
from services.auth_service import SessionContext


class EmployeeMgmtView(ctk.CTkFrame):
    """Staff administration interface for managing bank officers, tellers, and administrative users."""

    def __init__(self, master, current_session: SessionContext, **kwargs):
        super().__init__(master, fg_color=Theme.BG_DARK, **kwargs)

        self.current_session = current_session
        self._build_ui()
        self.refresh_employees()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(16, 12))

        ctk.CTkLabel(
            header,
            text="Staff & Employee Management",
            font=Theme.font_title(),
            text_color=Theme.TEXT_PRIMARY,
        ).pack(side="left")

        reg_btn = ctk.CTkButton(
            header,
            text="+ Add Staff Member",
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

        columns = ["Code", "Full Name", "Department", "Designation", "Email Address", "Status"]
        col_widths = [110, 140, 130, 130, 160, 90]

        self.table = DataTable(
            table_container,
            columns=columns,
            col_widths=col_widths,
            search_placeholder="Search staff by name, code, or department...",
            on_search=self.refresh_employees,
            on_row_click=self._on_row_click,
        )
        self.table.pack(fill="both", expand=True)

    def refresh_employees(self, query: str = ""):
        employees = employee_service.list_employees(search_query=query)
        rows = [
            {
                "id": e.id,
                "raw_emp": e,
                "Code": e.employee_code,
                "Full Name": e.full_name,
                "Department": e.department,
                "Designation": e.designation,
                "Email Address": e.email,
                "Status": e.status,
                "status": e.status,
            }
            for e in employees
        ]
        self.table.set_data(
            rows,
            key_fields=["Code", "Full Name", "Department", "Designation", "Email Address", "Status"],
        )

    def _on_row_click(self, row_data):
        emp = row_data.get("raw_emp")
        if not emp:
            return

        modal = ctk.CTkToplevel(self)
        modal.title(f"Staff Profile - {emp.full_name}")
        modal.geometry("460x420")
        modal.resizable(False, False)
        modal.configure(fg_color=Theme.BG_DARK)
        modal.transient(self)
        modal.grab_set()

        container = ctk.CTkFrame(modal, fg_color=Theme.SURFACE_CARD, corner_radius=12)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text=emp.full_name, font=Theme.font_subtitle(), text_color=Theme.TEXT_PRIMARY).pack(pady=(16, 2))
        ctk.CTkLabel(container, text=f"{emp.employee_code} • {emp.designation}", font=Theme.font_small(), text_color=Theme.ACCENT_CYAN).pack(pady=(0, 12))

        info_box = ctk.CTkFrame(container, fg_color=Theme.SURFACE_NAV, corner_radius=8)
        info_box.pack(fill="x", padx=16, pady=8)

        fields = [
            ("Department", emp.department),
            ("Email", emp.email),
            ("Phone", emp.phone),
            ("Status", emp.status),
        ]
        for k, v in fields:
            r = ctk.CTkFrame(info_box, fg_color="transparent")
            r.pack(fill="x", padx=12, pady=4)
            ctk.CTkLabel(r, text=k, width=110, font=Theme.font_small(), text_color=Theme.TEXT_SECONDARY, anchor="w").pack(side="left")
            ctk.CTkLabel(r, text=str(v), font=Theme.font_body_bold(), text_color=Theme.TEXT_PRIMARY, anchor="w").pack(side="left")

        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=20)

        def toggle_status():
            new_st = "TERMINATED" if emp.status == "ACTIVE" else "ACTIVE"
            ok, msg = employee_service.set_status(emp.id, new_st, self.current_session.user_id)
            if ok:
                messagebox.showinfo("Status Updated", msg)
                modal.destroy()
                self.refresh_employees()
            else:
                messagebox.showerror("Error", msg)

        st_btn_txt = "Deactivate Employee" if emp.status == "ACTIVE" else "Activate Employee"
        st_btn_col = Theme.DANGER if emp.status == "ACTIVE" else Theme.SUCCESS

        ctk.CTkButton(btn_row, text=st_btn_txt, fg_color=st_btn_col, corner_radius=8, command=toggle_status).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(btn_row, text="Close", fg_color="transparent", border_color=Theme.BORDER, border_width=1, corner_radius=8, command=modal.destroy).pack(side="right", padx=(4, 0))

    def _open_register_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Add Staff Member - Apex Horizon Bank")
        modal.geometry("480x560")
        modal.resizable(False, False)
        modal.configure(fg_color=Theme.BG_DARK)
        modal.transient(self)
        modal.grab_set()

        container = ctk.CTkFrame(modal, fg_color=Theme.SURFACE_CARD, corner_radius=12)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text="Staff Onboarding", font=Theme.font_subtitle(), text_color=Theme.TEXT_PRIMARY).pack(pady=(16, 12))

        form = ctk.CTkScrollableFrame(container, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=16)

        def make_entry(lbl_text, default=""):
            ctk.CTkLabel(form, text=lbl_text, font=Theme.font_small(), text_color=Theme.TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(4, 2))
            ent = ctk.CTkEntry(form, height=36, font=Theme.font_body(), fg_color=Theme.SURFACE_INPUT, border_color=Theme.BORDER, corner_radius=8)
            ent.pack(fill="x", pady=(0, 6))
            if default:
                ent.insert(0, default)
            return ent

        e_fn = make_entry("First Name *")
        e_ln = make_entry("Last Name *")
        e_dept = make_entry("Department *", "Retail Banking")
        e_desig = make_entry("Designation *", "Banking Officer")
        e_email = make_entry("Email Address *")
        e_phone = make_entry("Phone Number *", "+1-555-")
        e_user = make_entry("Username *")
        e_pwd = make_entry("Initial Password *", "Employee@123")

        err_lbl = ctk.CTkLabel(container, text="", font=Theme.font_small(), text_color=Theme.DANGER)
        err_lbl.pack(pady=4)

        def save():
            err_lbl.configure(text="")
            ok, emp, msg = employee_service.register_employee(
                first_name=e_fn.get(),
                last_name=e_ln.get(),
                department=e_dept.get(),
                designation=e_desig.get(),
                email=e_email.get(),
                phone=e_phone.get(),
                username=e_user.get().strip(),
                password=e_pwd.get().strip(),
                created_by_user_id=self.current_session.user_id,
            )
            if ok:
                messagebox.showinfo("Staff Added", f"Employee {emp.full_name} ({emp.employee_code}) added successfully!")
                modal.destroy()
                self.refresh_employees()
            else:
                err_lbl.configure(text=msg)

        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=16)

        ctk.CTkButton(btn_row, text="Register Employee", height=38, fg_color=Theme.SUCCESS, hover_color=Theme.SUCCESS_HOVER, font=Theme.font_body_bold(), corner_radius=8, command=save).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(btn_row, text="Cancel", height=38, fg_color="transparent", border_color=Theme.BORDER, border_width=1, font=Theme.font_body(), corner_radius=8, command=modal.destroy).pack(side="right", fill="x", expand=True, padx=(6, 0))

