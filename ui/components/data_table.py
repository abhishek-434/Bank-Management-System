"""Reusable modern data table widget with search, filtering, and action hooks."""
from typing import List, Dict, Any, Callable, Optional
import customtkinter as ctk
from ui.theme import Theme


class DataTable(ctk.CTkFrame):
    """Clean custom table with search bar, action bar, headers, and clickable rows."""

    def __init__(
        self,
        master,
        columns: List[str],
        col_widths: Optional[List[int]] = None,
        searchable: bool = True,
        search_placeholder: str = "Search records...",
        on_search: Optional[Callable[[str], None]] = None,
        on_row_click: Optional[Callable[[Dict[str, Any]], None]] = None,
        header_actions: Optional[List[tuple]] = None,  # [(label, callback, color)]
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

        self.columns = columns
        self.col_widths = col_widths or [100] * len(columns)
        self.searchable = searchable
        self.search_placeholder = search_placeholder
        self.on_search = on_search
        self.on_row_click = on_row_click
        self.header_actions = header_actions or []

        self.rows_data: List[Dict[str, Any]] = []

        self._build_toolbar()
        self._build_header()
        self._build_body()

    def _build_toolbar(self):
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=16, pady=(14, 10))

        if self.searchable:
            self.search_entry = ctk.CTkEntry(
                toolbar,
                placeholder_text=self.search_placeholder,
                width=260,
                height=34,
                font=Theme.font_body(),
                fg_color=Theme.SURFACE_INPUT,
                border_color=Theme.BORDER,
                corner_radius=8,
            )
            self.search_entry.pack(side="left")
            self.search_entry.bind("<KeyRelease>", self._on_search_key)

            clear_btn = ctk.CTkButton(
                toolbar,
                text="Clear",
                width=60,
                height=34,
                font=Theme.font_small(),
                fg_color="transparent",
                hover_color=Theme.SURFACE_NAV,
                text_color=Theme.TEXT_SECONDARY,
                command=self._clear_search,
            )
            clear_btn.pack(side="left", padx=6)

        # Header action buttons (e.g. Export, Add)
        for label, cmd, color in self.header_actions:
            btn = ctk.CTkButton(
                toolbar,
                text=label,
                height=34,
                font=Theme.font_body_bold(),
                fg_color=color or Theme.ACCENT_BLUE,
                hover_color=Theme.ACCENT_CYAN_HOVER,
                corner_radius=8,
                command=cmd,
            )
            btn.pack(side="right", padx=4)

    def _build_header(self):
        self.header_frame = ctk.CTkFrame(self, height=36, fg_color=Theme.SURFACE_NAV, corner_radius=6)
        self.header_frame.pack(fill="x", padx=12, pady=(0, 4))

        for idx, col_name in enumerate(self.columns):
            weight = self.col_widths[idx] if idx < len(self.col_widths) else 1
            self.header_frame.grid_columnconfigure(idx, weight=weight)
            lbl = ctk.CTkLabel(
                self.header_frame,
                text=col_name.upper(),
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11, weight="bold"),
                text_color=Theme.TEXT_SECONDARY,
                anchor="w",
            )
            lbl.grid(row=0, column=idx, padx=10, pady=8, sticky="w")

    def _build_body(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def set_data(self, rows: List[Dict[str, Any]], key_fields: List[str]) -> None:
        """Populate the table with data rows."""
        self.rows_data = rows

        # Clear existing rows
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not rows:
            empty_lbl = ctk.CTkLabel(
                self.scroll_frame,
                text="No records to display.",
                font=Theme.font_body(),
                text_color=Theme.TEXT_MUTED,
            )
            empty_lbl.pack(pady=40)
            return

        for r_idx, row in enumerate(rows):
            bg_color = Theme.SURFACE_ROW_ALT if (r_idx % 2 == 1) else Theme.SURFACE_CARD
            row_frame = ctk.CTkFrame(
                self.scroll_frame,
                height=38,
                fg_color=bg_color,
                corner_radius=6,
            )
            row_frame.pack(fill="x", pady=2)

            # Bind click
            if self.on_row_click:
                row_frame.bind("<Button-1>", lambda e, d=row: self.on_row_click(d))

            for c_idx, field in enumerate(key_fields):
                weight = self.col_widths[c_idx] if c_idx < len(self.col_widths) else 1
                row_frame.grid_columnconfigure(c_idx, weight=weight)

                val_text = str(row.get(field, ""))
                val_color = Theme.TEXT_PRIMARY

                # Status highlight
                if field in ("status", "Status"):
                    if val_text in ("ACTIVE", "SUCCESS", "COMPLETED", "APPROVED"):
                        val_color = Theme.SUCCESS
                    elif val_text in ("FROZEN", "PENDING", "APPLIED", "DORMANT"):
                        val_color = Theme.WARNING
                    elif val_text in ("CLOSED", "FAILED", "REJECTED", "REVERSED", "TERMINATED"):
                        val_color = Theme.DANGER

                lbl = ctk.CTkLabel(
                    row_frame,
                    text=val_text,
                    font=Theme.font_body(),
                    text_color=val_color,
                    anchor="w",
                )
                lbl.grid(row=0, column=c_idx, padx=10, pady=8, sticky="w")
                if self.on_row_click:
                    lbl.bind("<Button-1>", lambda e, d=row: self.on_row_click(d))

    def _on_search_key(self, event):
        query = self.search_entry.get()
        if self.on_search:
            self.on_search(query)

    def _clear_search(self):
        if hasattr(self, "search_entry"):
            self.search_entry.delete(0, "end")
        if self.on_search:
            self.on_search("")

