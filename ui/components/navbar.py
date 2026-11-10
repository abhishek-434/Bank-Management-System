"""Top navigation and session bar."""
import time
from datetime import datetime
from typing import Callable, Optional
import customtkinter as ctk
from ui.theme import Theme
from services.auth_service import SessionContext


class TopNavBar(ctk.CTkFrame):
    """Top bar displaying active session, current user badge, system clock, and quick actions."""

    def __init__(
        self,
        master,
        current_session: Optional[SessionContext],
        on_logout: Callable[[], None],
        on_change_password: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        super().__init__(
            master,
            height=60,
            fg_color=Theme.SURFACE_NAV,
            border_color=Theme.BORDER,
            border_width=1,
            corner_radius=0,
            **kwargs,
        )

        self.current_session = current_session
        self.on_logout = on_logout
        self.on_change_password = on_change_password

        self.pack_propagate(False)
        self._build_ui()
        self._update_clock()

    def _build_ui(self):
        # Left side: Page Title
        self.title_label = ctk.CTkLabel(
            self,
            text="Dashboard Overview",
            font=Theme.font_subtitle(),
            text_color=Theme.TEXT_PRIMARY,
        )
        self.title_label.pack(side="left", padx=24)

        # Right side: Logout button
        logout_btn = ctk.CTkButton(
            self,
            text="Sign Out",
            width=80,
            height=32,
            fg_color="transparent",
            hover_color=Theme.DANGER_HOVER,
            border_color=Theme.BORDER,
            border_width=1,
            text_color=Theme.TEXT_SECONDARY,
            font=Theme.font_small(),
            corner_radius=8,
            command=self.on_logout,
        )
        logout_btn.pack(side="right", padx=(12, 24))

        if self.on_change_password:
            pwd_btn = ctk.CTkButton(
                self,
                text="Key / Pwd",
                width=80,
                height=32,
                fg_color="transparent",
                hover_color=Theme.SURFACE_CARD,
                border_color=Theme.BORDER,
                border_width=1,
                text_color=Theme.TEXT_SECONDARY,
                font=Theme.font_small(),
                corner_radius=8,
                command=self.on_change_password,
            )
            pwd_btn.pack(side="right", padx=(6, 0))

        # Clock
        self.clock_label = ctk.CTkLabel(
            self,
            text="",
            font=Theme.font_small(),
            text_color=Theme.TEXT_MUTED,
        )
        self.clock_label.pack(side="right", padx=16)

        # User and Role badge
        if self.current_session:
            role_color = Theme.ACCENT_CYAN if self.current_session.is_admin else (
                Theme.SUCCESS if self.current_session.is_employee else Theme.ACCENT_BLUE
            )
            role_badge = ctk.CTkLabel(
                self,
                text=f" {self.current_session.role} ",
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=10, weight="bold"),
                text_color=Theme.TEXT_PRIMARY,
                fg_color=role_color,
                corner_radius=6,
            )
            role_badge.pack(side="right", padx=(6, 8))

            user_label = ctk.CTkLabel(
                self,
                text=self.current_session.display_name,
                font=Theme.font_body_bold(),
                text_color=Theme.TEXT_PRIMARY,
            )
            user_label.pack(side="right", padx=(12, 0))

    def set_page_title(self, title: str) -> None:
        """Update active page title."""
        self.title_label.configure(text=title)

    def _update_clock(self):
        """Dynamic clock updating every 1000ms."""
        now_str = datetime.now().strftime("%a, %b %d • %H:%M:%S")
        self.clock_label.configure(text=now_str)
        self.after(1000, self._update_clock)

