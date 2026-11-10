"""Main CustomTkinter desktop application window controller."""
import customtkinter as ctk
from typing import Optional
from config.settings import settings
from ui.theme import Theme
from ui.components.navbar import TopNavBar
from ui.components.sidebar import SidebarNav
from ui.components.modal import AlertModal
from ui.views.login_view import LoginView
from ui.views.admin_dashboard import AdminDashboardView
from ui.views.customer_mgmt_view import CustomerMgmtView
from ui.views.account_mgmt_view import AccountMgmtView
from ui.views.deposit_view import DepositView
from ui.views.withdrawal_view import WithdrawalView
from ui.views.transfer_view import TransferView
from ui.views.transaction_history import TransactionHistoryView
from ui.views.loan_mgmt_view import LoanMgmtView
from ui.views.reports_view import ReportsView
from ui.views.employee_mgmt_view import EmployeeMgmtView
from ui.views.audit_logs_view import AuditLogsView
from services.auth_service import auth_service, SessionContext


class BankingApp(ctk.CTk):
    """Core application window orchestrating authentication, navigation, and view switching."""

    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title("Apex Horizon Bank — Core Banking Management System")
        self.geometry(f"{settings.WINDOW_DEFAULT_WIDTH}x{settings.WINDOW_DEFAULT_HEIGHT}")
        self.minsize(1024, 680)
        self.configure(fg_color=Theme.BG_DARK)

        ctk.set_appearance_mode(settings.UI_APPEARANCE_MODE)
        ctk.set_default_color_theme(settings.UI_COLOR_THEME)

        self.current_session: Optional[SessionContext] = None
        self.active_view = None
        self.sidebar = None
        self.navbar = None

        self._show_login_screen()

    def _show_login_screen(self):
        """Display the centered authentication view."""
        self._clear_views()
        self.login_view = LoginView(self, on_login_success=self._on_login_success)
        self.login_view.pack(fill="both", expand=True)

    def _on_login_success(self, session: SessionContext):
        """Transition into authenticated workspace."""
        self.current_session = session
        if hasattr(self, "login_view") and self.login_view:
            self.login_view.destroy()
            self.login_view = None

        self._build_workspace()
        self.navigate_to("dashboard")

    def _build_workspace(self):
        """Construct main layout: Sidebar on left, TopNavBar & Content on right."""
        # Top-level layout grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)  # Sidebar
        self.grid_columnconfigure(1, weight=1)  # Main View Area

        # 1. Left Sidebar
        self.sidebar = SidebarNav(
            self,
            current_session=self.current_session,
            on_navigate=self.navigate_to,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # 2. Right Pane (TopNavBar + Content Container)
        self.right_pane = ctk.CTkFrame(self, fg_color=Theme.BG_DARK)
        self.right_pane.grid(row=0, column=1, sticky="nsew")
        self.right_pane.grid_rowconfigure(0, weight=0)  # Navbar
        self.right_pane.grid_rowconfigure(1, weight=1)  # Content
        self.right_pane.grid_columnconfigure(0, weight=1)

        # Top Navigation Bar
        self.navbar = TopNavBar(
            self.right_pane,
            current_session=self.current_session,
            on_logout=self._handle_logout,
            on_change_password=self._open_change_password_modal,
        )
        self.navbar.grid(row=0, column=0, sticky="ew")

        # Content Frame
        self.content_container = ctk.CTkFrame(self.right_pane, fg_color=Theme.BG_DARK)
        self.content_container.grid(row=1, column=0, sticky="nsew")
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

    def navigate_to(self, view_id: str):
        """Switch active content view."""
        if self.active_view:
            self.active_view.destroy()
            self.active_view = None

        view_map = {
            "dashboard": (AdminDashboardView, "Dashboard Overview"),
            "customers": (CustomerMgmtView, "Customer Profile Management"),
            "accounts": (AccountMgmtView, "Bank Accounts Management"),
            "deposit": (DepositView, "Deposit Cash & Funds"),
            "withdrawal": (WithdrawalView, "Withdraw Cash & Funds"),
            "transfer": (TransferView, "Internal Fund Transfer"),
            "transactions": (TransactionHistoryView, "Financial Ledger & History"),
            "loans": (LoanMgmtView, "Loan Operations & Repayments"),
            "reports": (ReportsView, "Reports & Portfolio Analytics"),
            "employees": (EmployeeMgmtView, "Staff & Employee Administration"),
            "audit": (AuditLogsView, "System Audit Trail"),
        }

        entry = view_map.get(view_id)
        if not entry:
            return

        view_cls, title = entry
        self.navbar.set_page_title(title)
        self.sidebar.set_active(view_id)

        self.active_view = view_cls(self.content_container, current_session=self.current_session)
        self.active_view.grid(row=0, column=0, sticky="nsew")

    def _handle_logout(self):
        """Sign out active user and reset to login view."""
        auth_service.logout()
        self.current_session = None

        if self.sidebar:
            self.sidebar.destroy()
            self.sidebar = None
        if hasattr(self, "right_pane") and self.right_pane:
            self.right_pane.destroy()
            self.right_pane = None

        self._show_login_screen()

    def _open_change_password_modal(self):
        """Modal to change active user password."""
        modal = ctk.CTkToplevel(self)
        modal.title("Change Password - Apex Horizon Bank")
        modal.geometry("440x380")
        modal.resizable(False, False)
        modal.configure(fg_color=Theme.BG_DARK)
        modal.transient(self)
        modal.grab_set()

        container = ctk.CTkFrame(modal, fg_color=Theme.SURFACE_CARD, corner_radius=12)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text="Change Password", font=Theme.font_subtitle(), text_color=Theme.TEXT_PRIMARY).pack(pady=(16, 12))

        def make_entry(lbl_text):
            ctk.CTkLabel(container, text=lbl_text, font=Theme.font_small(), text_color=Theme.TEXT_SECONDARY, anchor="w").pack(fill="x", padx=20, pady=(2, 2))
            ent = ctk.CTkEntry(container, show="•", height=36, font=Theme.font_body(), fg_color=Theme.SURFACE_INPUT, border_color=Theme.BORDER, corner_radius=8)
            ent.pack(fill="x", padx=20, pady=(0, 6))
            return ent

        e_cur = make_entry("Current Password *")
        e_new = make_entry("New Password *")
        e_cnf = make_entry("Confirm New Password *")

        err_lbl = ctk.CTkLabel(container, text="", font=Theme.font_small(), text_color=Theme.DANGER)
        err_lbl.pack(pady=4)

        def save_pwd():
            ok, msg = auth_service.change_password(
                user_id=self.current_session.user_id,
                current_password=e_cur.get().strip(),
                new_password=e_new.get().strip(),
                confirm_password=e_cnf.get().strip(),
            )
            if ok:
                AlertModal.show_info("Success", msg)
                modal.destroy()
            else:
                err_lbl.configure(text=msg)

        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=12)

        ctk.CTkButton(btn_row, text="Update Password", height=38, fg_color=Theme.ACCENT_BLUE, hover_color=Theme.ACCENT_CYAN_HOVER, font=Theme.font_body_bold(), corner_radius=8, command=save_pwd).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(btn_row, text="Cancel", height=38, fg_color="transparent", border_color=Theme.BORDER, border_width=1, corner_radius=8, command=modal.destroy).pack(side="right", fill="x", expand=True, padx=(4, 0))

    def _clear_views(self):
        for widget in self.winfo_children():
            widget.destroy()


def start_app():
    """Application entry point."""
    app = BankingApp()
    app.mainloop()


if __name__ == "__main__":
    start_app()

