"""Sidebar navigation component tailored to user permissions."""
from typing import Callable, Dict, List
import customtkinter as ctk
from ui.theme import Theme
from services.auth_service import SessionContext


class SidebarNav(ctk.CTkFrame):
    """Modern left sidebar with brand logo and role-based navigation tabs."""

    def __init__(
        self,
        master,
        current_session: SessionContext,
        on_navigate: Callable[[str], None],
        **kwargs,
    ):
        super().__init__(
            master,
            width=240,
            fg_color=Theme.SURFACE_NAV,
            border_color=Theme.BORDER,
            border_width=1,
            corner_radius=0,
            **kwargs,
        )

        self.current_session = current_session
        self.on_navigate = on_navigate
        self.active_tab: str = ""
        self.nav_buttons: Dict[str, ctk.CTkButton] = {}

        self.pack_propagate(False)
        self._build_header()
        self._build_nav_links()
        self._build_footer()

    def _build_header(self):
        brand_frame = ctk.CTkFrame(self, fg_color="transparent")
        brand_frame.pack(fill="x", padx=16, pady=(20, 16))

        logo_label = ctk.CTkLabel(
            brand_frame,
            text="⬢ APEX BANK",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=18, weight="bold"),
            text_color=Theme.ACCENT_CYAN,
            anchor="w",
        )
        logo_label.pack(fill="x")

        sub_label = ctk.CTkLabel(
            brand_frame,
            text="Core Banking Management",
            font=Theme.font_small(),
            text_color=Theme.TEXT_MUTED,
            anchor="w",
        )
        sub_label.pack(fill="x")

        separator = ctk.CTkFrame(self, height=1, fg_color=Theme.BORDER)
        separator.pack(fill="x", padx=16, pady=(0, 12))

    def _build_nav_links(self):
        self.scroll_nav = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_nav.pack(fill="both", expand=True, padx=8, pady=4)

        tabs = self._get_tabs_for_role()
        for tab_id, tab_label, icon in tabs:
            btn = ctk.CTkButton(
                self.scroll_nav,
                text=f"  {icon}  {tab_label}",
                anchor="w",
                height=40,
                corner_radius=8,
                fg_color="transparent",
                hover_color=Theme.SURFACE_CARD,
                text_color=Theme.TEXT_SECONDARY,
                font=Theme.font_body(),
                command=lambda tid=tab_id: self._handle_click(tid),
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[tab_id] = btn

    def _get_tabs_for_role(self) -> List[tuple]:
        if self.current_session.is_admin:
            return [
                ("dashboard", "Dashboard", "📊"),
                ("customers", "Customers", "👥"),
                ("accounts", "Bank Accounts", "💳"),
                ("deposit", "Deposit", "📥"),
                ("withdrawal", "Withdrawal", "📤"),
                ("transfer", "Fund Transfer", "🔁"),
                ("transactions", "Transactions", "📑"),
                ("loans", "Loan Operations", "💼"),
                ("reports", "Reports & Analytics", "📈"),
                ("employees", "Staff Management", "🛡"),
                ("audit", "Audit Trail", "🔍"),
            ]
        elif self.current_session.is_employee:
            return [
                ("dashboard", "Dashboard", "📊"),
                ("customers", "Customers", "👥"),
                ("accounts", "Bank Accounts", "💳"),
                ("deposit", "Deposit Funds", "📥"),
                ("withdrawal", "Withdraw Funds", "📤"),
                ("transfer", "Internal Transfer", "🔁"),
                ("transactions", "Transactions", "📑"),
                ("loans", "Loan Operations", "💼"),
                ("reports", "Analytics Reports", "📈"),
            ]
        else:  # Customer portal
            return [
                ("dashboard", "My Overview", "📊"),
                ("accounts", "My Accounts", "💳"),
                ("transfer", "Transfer Money", "🔁"),
                ("transactions", "Transaction History", "📑"),
                ("loans", "My Loan Status", "💼"),
            ]

    def _handle_click(self, tab_id: str):
        self.set_active(tab_id)
        self.on_navigate(tab_id)

    def set_active(self, tab_id: str):
        """Highlight active tab."""
        self.active_tab = tab_id
        for tid, btn in self.nav_buttons.items():
            if tid == tab_id:
                btn.configure(
                    fg_color=Theme.SURFACE_CARD,
                    border_color=Theme.ACCENT_CYAN,
                    border_width=1,
                    text_color=Theme.TEXT_PRIMARY,
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    border_width=0,
                    text_color=Theme.TEXT_SECONDARY,
                )

    def _build_footer(self):
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.pack(fill="x", side="bottom", padx=16, pady=12)

        env_tag = ctk.CTkLabel(
            footer_frame,
            text="SIMULATION MODE • v1.0",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=9),
            text_color=Theme.TEXT_MUTED,
            anchor="center",
        )
        env_tag.pack(fill="x")

