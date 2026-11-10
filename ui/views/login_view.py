"""Modern centered authentication view."""
from typing import Callable, Optional
import customtkinter as ctk
from ui.theme import Theme
from services.auth_service import auth_service, SessionContext


class LoginView(ctk.CTkFrame):
    """Authentication screen featuring credentials input and quick demo shortcuts."""

    def __init__(self, master, on_login_success: Callable[[SessionContext], None], **kwargs):
        super().__init__(master, fg_color=Theme.BG_DARK, **kwargs)

        self.on_login_success = on_login_success
        self.show_password = False

        self._build_ui()

    def _build_ui(self):
        # Center container
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(
            self,
            width=440,
            fg_color=Theme.SURFACE_CARD,
            border_color=Theme.BORDER,
            border_width=1,
            corner_radius=16,
        )
        card.grid(row=0, column=0, padx=20, pady=20)

        # Brand header
        logo_lbl = ctk.CTkLabel(
            card,
            text="⬢ APEX HORIZON BANK",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=22, weight="bold"),
            text_color=Theme.ACCENT_CYAN,
        )
        logo_lbl.pack(pady=(28, 4))

        sub_lbl = ctk.CTkLabel(
            card,
            text="Core Banking Management System",
            font=Theme.font_body(),
            text_color=Theme.TEXT_SECONDARY,
        )
        sub_lbl.pack(pady=(0, 20))

        sep = ctk.CTkFrame(card, height=1, fg_color=Theme.BORDER)
        sep.pack(fill="x", padx=30, pady=(0, 20))

        # Input fields container
        form_frame = ctk.CTkFrame(card, fg_color="transparent")
        form_frame.pack(fill="x", padx=36)

        # Username
        u_lbl = ctk.CTkLabel(form_frame, text="Username or Account ID", font=Theme.font_small(), text_color=Theme.TEXT_SECONDARY, anchor="w")
        u_lbl.pack(fill="x", pady=(0, 4))

        self.username_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Enter your username",
            height=40,
            font=Theme.font_body(),
            fg_color=Theme.SURFACE_INPUT,
            border_color=Theme.BORDER,
            corner_radius=8,
        )
        self.username_entry.pack(fill="x", pady=(0, 14))

        # Password
        p_lbl = ctk.CTkLabel(form_frame, text="Password", font=Theme.font_small(), text_color=Theme.TEXT_SECONDARY, anchor="w")
        p_lbl.pack(fill="x", pady=(0, 4))

        pwd_row = ctk.CTkFrame(form_frame, fg_color="transparent")
        pwd_row.pack(fill="x", pady=(0, 16))

        self.password_entry = ctk.CTkEntry(
            pwd_row,
            placeholder_text="••••••••",
            show="•",
            height=40,
            font=Theme.font_body(),
            fg_color=Theme.SURFACE_INPUT,
            border_color=Theme.BORDER,
            corner_radius=8,
        )
        self.password_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.toggle_btn = ctk.CTkButton(
            pwd_row,
            text="👁",
            width=40,
            height=40,
            fg_color=Theme.SURFACE_INPUT,
            border_color=Theme.BORDER,
            border_width=1,
            hover_color=Theme.SURFACE_NAV,
            text_color=Theme.TEXT_SECONDARY,
            corner_radius=8,
            command=self._toggle_password_visibility,
        )
        self.toggle_btn.pack(side="right")

        # Status Message
        self.msg_label = ctk.CTkLabel(
            form_frame,
            text="",
            font=Theme.font_small(),
            text_color=Theme.DANGER,
            wraplength=340,
        )
        self.msg_label.pack(fill="x", pady=(0, 8))

        # Sign In Button
        self.login_btn = ctk.CTkButton(
            form_frame,
            text="Sign In to Account",
            height=42,
            font=Theme.font_body_bold(),
            fg_color=Theme.ACCENT_BLUE,
            hover_color=Theme.ACCENT_CYAN_HOVER,
            corner_radius=8,
            command=self._execute_login,
        )
        self.login_btn.pack(fill="x", pady=(0, 16))

        # Bind Enter key
        self.username_entry.bind("<Return>", lambda e: self._execute_login())
        self.password_entry.bind("<Return>", lambda e: self._execute_login())

        # Demo credentials shortcuts
        demo_box = ctk.CTkFrame(card, fg_color=Theme.SURFACE_NAV, corner_radius=10)
        demo_box.pack(fill="x", padx=36, pady=(0, 24))

        demo_title = ctk.CTkLabel(
            demo_box,
            text="DEMONSTRATION SHORTCUTS",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=9, weight="bold"),
            text_color=Theme.TEXT_MUTED,
        )
        demo_title.pack(pady=(10, 6))

        btn_grid = ctk.CTkFrame(demo_box, fg_color="transparent")
        btn_grid.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkButton(
            btn_grid,
            text="Admin",
            height=28,
            font=Theme.font_small(),
            fg_color=Theme.SURFACE_CARD,
            hover_color=Theme.ACCENT_BLUE,
            corner_radius=6,
            command=lambda: self._fill_demo("admin", "Admin@123"),
        ).pack(side="left", fill="x", expand=True, padx=2)

        ctk.CTkButton(
            btn_grid,
            text="Employee",
            height=28,
            font=Theme.font_small(),
            fg_color=Theme.SURFACE_CARD,
            hover_color=Theme.SUCCESS_HOVER,
            corner_radius=6,
            command=lambda: self._fill_demo("employee1", "Employee@123"),
        ).pack(side="left", fill="x", expand=True, padx=2)

        ctk.CTkButton(
            btn_grid,
            text="Customer",
            height=28,
            font=Theme.font_small(),
            fg_color=Theme.SURFACE_CARD,
            hover_color=Theme.ACCENT_CYAN_HOVER,
            corner_radius=6,
            command=lambda: self._fill_demo("customer1", "Customer@123"),
        ).pack(side="left", fill="x", expand=True, padx=2)

    def _fill_demo(self, username: str, pwd: str):
        self.username_entry.delete(0, "end")
        self.username_entry.insert(0, username)
        self.password_entry.delete(0, "end")
        self.password_entry.insert(0, pwd)
        self.msg_label.configure(text="")

    def _toggle_password_visibility(self):
        self.show_password = not self.show_password
        self.password_entry.configure(show="" if self.show_password else "•")
        self.toggle_btn.configure(text="🔒" if self.show_password else "👁")

    def _execute_login(self):
        u = self.username_entry.get().strip()
        p = self.password_entry.get().strip()
        self.msg_label.configure(text="")

        if not u or not p:
            self.msg_label.configure(text="Please enter both username and password.", text_color=Theme.DANGER)
            return

        success, session_ctx, msg = auth_service.login(u, p)
        if success and session_ctx:
            self.on_login_success(session_ctx)
        else:
            self.msg_label.configure(text=msg, text_color=Theme.DANGER)

