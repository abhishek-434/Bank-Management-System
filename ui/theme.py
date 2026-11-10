"""UI styling constants and theme design system."""
import customtkinter as ctk


class Theme:
    """Color palette, font definitions, and standard widget metrics."""

    # Color Palette (Navy Blue, White, Subtle Cyan)
    BG_DARK = "#0B132B"          # Deep Navy primary background
    SURFACE_NAV = "#141D35"      # Sidebar & navbar surface
    SURFACE_CARD = "#1C2744"     # Card containers & frames
    SURFACE_INPUT = "#111827"    # Text fields & dropdowns
    SURFACE_ROW_ALT = "#162039"  # Alternating table rows
    BORDER = "#2E3D60"           # Subtle borders

    # Accents
    ACCENT_CYAN = "#00B4D8"      # Primary cyan accent
    ACCENT_CYAN_HOVER = "#48CAE4"# Hover cyan
    ACCENT_BLUE = "#0077B6"      # Primary action button
    ACCENT_BLUE_HOVER = "#0288D1"

    # Status & Feedback
    SUCCESS = "#2EC4B6"          # Emerald cyan
    SUCCESS_HOVER = "#24A094"
    WARNING = "#FF9F1C"          # Amber orange
    DANGER = "#E63946"           # Coral red
    DANGER_HOVER = "#D62839"

    # Text Colors
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#A0AEC0"
    TEXT_MUTED = "#64748B"

    # Fonts
    FONT_FAMILY = "Segoe UI"

    @classmethod
    def font_title(cls) -> ctk.CTkFont:
        return ctk.CTkFont(family=cls.FONT_FAMILY, size=22, weight="bold")

    @classmethod
    def font_subtitle(cls) -> ctk.CTkFont:
        return ctk.CTkFont(family=cls.FONT_FAMILY, size=15, weight="bold")

    @classmethod
    def font_section(cls) -> ctk.CTkFont:
        return ctk.CTkFont(family=cls.FONT_FAMILY, size=13, weight="bold")

    @classmethod
    def font_body(cls) -> ctk.CTkFont:
        return ctk.CTkFont(family=cls.FONT_FAMILY, size=12)

    @classmethod
    def font_body_bold(cls) -> ctk.CTkFont:
        return ctk.CTkFont(family=cls.FONT_FAMILY, size=12, weight="bold")

    @classmethod
    def font_small(cls) -> ctk.CTkFont:
        return ctk.CTkFont(family=cls.FONT_FAMILY, size=10)

    @classmethod
    def font_kpi_value(cls) -> ctk.CTkFont:
        return ctk.CTkFont(family=cls.FONT_FAMILY, size=24, weight="bold")

