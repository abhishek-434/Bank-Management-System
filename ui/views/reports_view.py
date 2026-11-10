"""Reports and financial analytics interface."""
from datetime import datetime
from tkinter import messagebox, filedialog
import customtkinter as ctk
import pandas as pd
from ui.theme import Theme
from ui.components.stat_card import StatCard
from ui.components.chart_frame import ChartFrame
from ui.components.data_table import DataTable
from services.report_service import report_service
from services.auth_service import SessionContext
from utils.formatters import format_currency
from config.settings import settings
import matplotlib.pyplot as plt


class ReportsView(ctk.CTkScrollableFrame):
    """Analytics and reporting dashboard supporting multi-period summaries and data exports."""

    def __init__(self, master, current_session: SessionContext, **kwargs):
        super().__init__(master, fg_color=Theme.BG_DARK, **kwargs)

        self.current_session = current_session

        self._build_header()
        self._build_summary_cards()
        self._build_charts()
        self._build_breakdown_table()
        self.refresh_reports()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(16, 12))

        ctk.CTkLabel(
            header,
            text="Financial Reports & Analytics",
            font=Theme.font_title(),
            text_color=Theme.TEXT_PRIMARY,
        ).pack(side="left")

        export_btn = ctk.CTkButton(
            header,
            text="Export Master CSV Report",
            height=34,
            font=Theme.font_body_bold(),
            fg_color=Theme.ACCENT_BLUE,
            hover_color=Theme.ACCENT_CYAN_HOVER,
            corner_radius=8,
            command=self._export_full_report,
        )
        export_btn.pack(side="right")

    def _build_summary_cards(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=20, pady=(0, 16))

        for i in range(4):
            container.grid_columnconfigure(i, weight=1)

        self.c_dep = StatCard(container, title="Gross Deposits", value="$0.00", icon="📥", accent_color=Theme.SUCCESS)
        self.c_dep.grid(row=0, column=0, padx=6, pady=6, sticky="ew")

        self.c_with = StatCard(container, title="Gross Withdrawals", value="$0.00", icon="📤", accent_color=Theme.DANGER)
        self.c_with.grid(row=0, column=1, padx=6, pady=6, sticky="ew")

        self.c_trf = StatCard(container, title="Transfer Volume", value="$0.00", icon="🔁", accent_color=Theme.ACCENT_CYAN)
        self.c_trf.grid(row=0, column=2, padx=6, pady=6, sticky="ew")

        self.c_vault = StatCard(container, title="Total Vault Reserve", value="$0.00", icon="🏦", accent_color=Theme.WARNING)
        self.c_vault.grid(row=0, column=3, padx=6, pady=6, sticky="ew")

    def _build_charts(self):
        box = ctk.CTkFrame(self, fg_color="transparent")
        box.pack(fill="x", padx=20, pady=(0, 16))
        box.grid_columnconfigure(0, weight=1)

        self.chart_frame = ChartFrame(box, title="Historical Inflow vs Outflow Comparison", height=320)
        self.chart_frame.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")

    def _build_breakdown_table(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=26, pady=(0, 24))

        ctk.CTkLabel(
            container,
            text="ACCOUNT PRODUCT PERFORMANCE BREAKDOWN",
            font=Theme.font_section(),
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        columns = ["Product Name", "Total Accounts", "Aggregated Balance", "Portfolio Share"]
        col_widths = [160, 120, 140, 120]
        self.breakdown_table = DataTable(container, columns=columns, col_widths=col_widths, searchable=False)
        self.breakdown_table.pack(fill="both", expand=True)

    def refresh_reports(self):
        kpis = report_service.get_kpi_summary()
        self.c_dep.update_value(format_currency(kpis["total_deposits"]))
        self.c_with.update_value(format_currency(kpis["total_withdrawals"]))
        self.c_trf.update_value(format_currency(kpis["total_transfer_volume"]))
        self.c_vault.update_value(format_currency(kpis["total_bank_balance"]))

        # Product breakdown
        df_dist = report_service.get_account_type_distribution()
        total_bal = df_dist["Total Balance"].sum() if not df_dist.empty else 1.0
        rows = []
        for _, r in df_dist.iterrows():
            share = (r["Total Balance"] / total_bal * 100) if total_bal > 0 else 0
            rows.append({
                "Product Name": r["Account Type"],
                "Total Accounts": str(r["Count"]),
                "Aggregated Balance": f"${r['Total Balance']:,.2f}",
                "Portfolio Share": f"{share:.1f}%",
            })
        self.breakdown_table.set_data(
            rows,
            key_fields=["Product Name", "Total Accounts", "Aggregated Balance", "Portfolio Share"],
        )

        # Plot Inflow vs Outflow Line Chart
        self._plot_flow_chart()

    def _plot_flow_chart(self):
        df = report_service.get_monthly_transaction_stats(months=8)

        fig, ax = plt.subplots(figsize=(7, 3.2), dpi=90)
        fig.patch.set_facecolor(Theme.SURFACE_CARD)
        ax.set_facecolor(Theme.SURFACE_NAV)

        if not df.empty and "Month" in df.columns:
            months = df["Month"]
            dep = df["Deposits"] if "Deposits" in df.columns else [0] * len(months)
            wth = df["Withdrawals"] if "Withdrawals" in df.columns else [0] * len(months)
            trf = df["Transfers"] if "Transfers" in df.columns else [0] * len(months)

            ax.plot(months, dep, marker="o", color=Theme.SUCCESS, label="Inflows (Deposits)", linewidth=2)
            ax.plot(months, wth, marker="s", color=Theme.DANGER, label="Outflows (Withdrawals)", linewidth=2)
            ax.plot(months, trf, marker="^", color=Theme.ACCENT_CYAN, label="Transfers", linewidth=2)
        else:
            ax.text(0.5, 0.5, "No financial transactions recorded yet.", color=Theme.TEXT_MUTED, ha="center")

        ax.tick_params(colors=Theme.TEXT_SECONDARY, labelsize=8)
        ax.spines["bottom"].set_color(Theme.BORDER)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(Theme.BORDER)
        ax.grid(color=Theme.BORDER, linestyle="--", alpha=0.4)
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(facecolor=Theme.SURFACE_CARD, edgecolor=Theme.BORDER, labelcolor=Theme.TEXT_PRIMARY, fontsize=8)

        plt.tight_layout()
        self.chart_frame.render_figure(fig)

    def _export_full_report(self):
        dest = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Spreadsheet", "*.csv")],
            initialdir=str(settings.EXPORTS_DIR),
            initialfile=f"BMS_Executive_Report_{datetime.now().strftime('%Y%m%d')}.csv",
        )
        if dest:
            try:
                report_service.export_transactions_to_csv(dest)
                messagebox.showinfo("Export Successful", f"Executive report saved to:\n{dest}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to save report:\n{e}")
