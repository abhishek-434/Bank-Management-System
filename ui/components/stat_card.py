"""Reusable KPI summary card component."""
import customtkinter as ctk
from ui.theme import Theme


class StatCard(ctk.CTkFrame):
    """Modern financial KPI card displaying an icon, label, large value, and subtext."""

    def __init__(
        self,
        master,
        title: str,
        value: str,
        subtext: str = "",
        icon: str = "◆",
        accent_color: str = Theme.ACCENT_CYAN,
        **kwargs,
    ):
        super().__init__(
            master,
            fg_color=Theme.SURFACE_CARD,
            border_color=Theme.BORDER,
            border_width=1,
            corner_radius=12,
            **kwargs,
        )

        self.grid_columnconfigure(0, weight=1)

        # Header row (Icon + Title)
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=16, pady=(14, 4), sticky="ew")

        icon_label = ctk.CTkLabel(
            header_frame,
            text=icon,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=16, weight="bold"),
            text_color=accent_color,
        )
        icon_label.pack(side="left", padx=(0, 8))

        title_label = ctk.CTkLabel(
            header_frame,
            text=title.upper(),
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
            text_color=Theme.TEXT_SECONDARY,
        )
        title_label.pack(side="left")

        # Big Value
        self.value_label = ctk.CTkLabel(
            self,
            text=value,
            font=Theme.font_kpi_value(),
            text_color=Theme.TEXT_PRIMARY,
            anchor="w",
        )
        self.value_label.grid(row=1, column=0, padx=16, pady=2, sticky="w")

        # Subtext / Delta
        self.subtext_label = ctk.CTkLabel(
            self,
            text=subtext,
            font=Theme.font_small(),
            text_color=Theme.TEXT_MUTED,
            anchor="w",
        )
        self.subtext_label.grid(row=2, column=0, padx=16, pady=(0, 14), sticky="w")

    def update_value(self, new_value: str, new_subtext: str = None) -> None:
        """Dynamically update card text."""
        self.value_label.configure(text=new_value)
        if new_subtext is not None:
            self.subtext_label.configure(text=new_subtext)

