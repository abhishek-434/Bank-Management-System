"""Embedded Matplotlib chart widget styled for the dark navy banking theme."""
import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ui.theme import Theme


class ChartFrame(ctk.CTkFrame):
    """Reusable frame embedding an interactive Matplotlib chart canvas."""

    def __init__(self, master, title: str = "", **kwargs):
        super().__init__(
            master,
            fg_color=Theme.SURFACE_CARD,
            border_color=Theme.BORDER,
            border_width=1,
            corner_radius=12,
            **kwargs,
        )

        self.chart_title = title
        self.figure = None
        self.canvas = None

        self._build_header()
        self._build_canvas()

    def _build_header(self):
        if self.chart_title:
            title_lbl = ctk.CTkLabel(
                self,
                text=self.chart_title.upper(),
                font=Theme.font_section(),
                text_color=Theme.TEXT_SECONDARY,
                anchor="w",
            )
            title_lbl.pack(fill="x", padx=16, pady=(12, 6))

    def _build_canvas(self):
        self.chart_container = ctk.CTkFrame(self, fg_color="transparent")
        self.chart_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def render_figure(self, fig: plt.Figure) -> None:
        """Render a Matplotlib figure onto the Tkinter canvas."""
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            plt.close(self.figure)

        self.figure = fig
        # Apply dark styling to figure
        fig.patch.set_facecolor(Theme.SURFACE_CARD)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.chart_container)
        self.canvas.draw()
        widget = self.canvas.get_tk_widget()
        widget.pack(fill="both", expand=True)

    def destroy(self):
        if self.figure:
            plt.close(self.figure)
        super().destroy()

