"""Audit trail inspection view for security, compliance, and activity auditing."""
from tkinter import messagebox
import customtkinter as ctk
from ui.theme import Theme
from ui.components.data_table import DataTable
from services.audit_service import audit_service
from services.auth_service import SessionContext


class AuditLogsView(ctk.CTkFrame):
    """System-wide audit trail inspection interface."""

    def __init__(self, master, current_session: SessionContext, **kwargs):
        super().__init__(master, fg_color=Theme.BG_DARK, **kwargs)

        self.current_session = current_session
        self.action_filter = ""

        self._build_ui()
        self.refresh_logs()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(16, 12))

        ctk.CTkLabel(
            header,
            text="System Audit Logs & Compliance Trail",
            font=Theme.font_title(),
            text_color=Theme.TEXT_PRIMARY,
        ).pack(side="left")

        # Table
        table_container = ctk.CTkFrame(self, fg_color="transparent")
        table_container.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        columns = ["Timestamp (UTC)", "Action Type", "Target Entity", "Target ID", "IP Address"]
        col_widths = [140, 150, 110, 120, 100]

        self.table = DataTable(
            table_container,
            columns=columns,
            col_widths=col_widths,
            search_placeholder="Search by action name...",
            on_search=self._on_search,
            on_row_click=self._on_row_click,
        )
        self.table.pack(fill="both", expand=True)

    def refresh_logs(self, query: str = ""):
        logs = audit_service.get_logs(action_filter=query, limit=150)
        rows = [
            {
                "raw_log": l,
                "Timestamp (UTC)": l.timestamp.strftime("%Y-%m-%d %H:%M:%S") if l.timestamp else "",
                "Action Type": l.action,
                "Target Entity": l.target_entity,
                "Target ID": l.target_id or "N/A",
                "IP Address": l.ip_address,
            }
            for l in logs
        ]
        self.table.set_data(
            rows,
            key_fields=["Timestamp (UTC)", "Action Type", "Target Entity", "Target ID", "IP Address"],
        )

    def _on_search(self, query: str):
        self.refresh_logs(query)

    def _on_row_click(self, row_data):
        l = row_data.get("raw_log")
        if not l:
            return

        modal = ctk.CTkToplevel(self)
        modal.title(f"Audit Log - {l.action}")
        modal.geometry("480x380")
        modal.resizable(False, False)
        modal.configure(fg_color=Theme.BG_DARK)
        modal.transient(self)
        modal.grab_set()

        container = ctk.CTkFrame(modal, fg_color=Theme.SURFACE_CARD, corner_radius=12)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text=f"Audit Event: {l.action}", font=Theme.font_subtitle(), text_color=Theme.TEXT_PRIMARY).pack(pady=(16, 4))
        ctk.CTkLabel(container, text=f"Target: {l.target_entity} ({l.target_id or 'N/A'})", font=Theme.font_small(), text_color=Theme.ACCENT_CYAN).pack(pady=(0, 12))

        det_box = ctk.CTkTextbox(container, height=160, font=ctk.CTkFont(family="Consolas", size=11), fg_color=Theme.SURFACE_INPUT, text_color=Theme.TEXT_PRIMARY, corner_radius=8)
        det_box.pack(fill="both", expand=True, padx=16, pady=4)
        det_box.insert("1.0", l.details or "No details payload")
        det_box.configure(state="disabled")

        ctk.CTkButton(container, text="Close", width=90, fg_color=Theme.SURFACE_NAV, corner_radius=8, command=modal.destroy).pack(pady=12)

