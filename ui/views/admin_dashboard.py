"""Executive and administrative dashboard with live KPIs and embedded Matplotlib charts."""
from decimal import Decimal
import customtkinter as ctk
import matplotlib.pyplot as plt
import pandas as pd
from ui.theme import Theme
from ui.components.stat_card import StatCard
from ui.components.chart_frame import ChartFrame
from ui.components.data_table import DataTable
from services.report_service import report_service
from services.transaction_service import transaction_service
from services.auth_service import SessionContext
from utils.formatters import format_currency


class AdminDashboardView(ctk.CTkScrollableFrame):
    """Rich interactive dashboard with summary cards, charts, and recent activity."""

    def __init__(self, master, current_session: SessionContext, **kwargs):
        super().__init__(master, fg_color=Theme.BG_DARK, **kwargs)

        self.current_session = current_session
        self.stat_cards = {}

        self._build_header()
        self._build_kpi_cards()
        self._build_charts_row()
        self._build_recent_transactions()
        self.refresh_data()

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(16, 12))

        title_lbl = ctk.CTkLabel(
            header_frame,
            text=f"Welcome back, {self.current_session.display_name}",
            font=Theme.font_title(),
            text_color=Theme.TEXT_PRIMARY,
        )
        title_lbl.pack(side="left")

        refresh_btn = ctk.CTkButton(
            header_frame,
            text="⟳ Refresh Data",
            width=120,
            height=34,
            font=Theme.font_body_bold(),
            fg_color=Theme.SURFACE_CARD,
            hover_color=Theme.SURFACE_NAV,
            border_color=Theme.BORDER,
            border_width=1,
            corner_radius=8,
            command=self.refresh_data,
        )
        refresh_btn.pack(side="right")

    def _build_kpi_cards(self):
        kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        kpi_container.pack(fill="x", padx=20, pady=(0, 16))

        for i in range(4):
            kpi_container.grid_columnconfigure(i, weight=1)

        # Card 1: Total Customers
        c1 = StatCard(kpi_container, title="Total Customers", value="0", subtext="Active verified entities", icon="👥")
        c1.grid(row=0, column=0, padx=6, pady=6, sticky="ew")
        self.stat_cards["customers"] = c1

        # Card 2: Active Accounts
        c2 = StatCard(kpi_container, title="Active Accounts", value="0", subtext="Operational accounts", icon="💳", accent_color=Theme.SUCCESS)
        c2.grid(row=0, column=1, padx=6, pady=6, sticky="ew")
        self.stat_cards["accounts"] = c2

        # Card 3: Total Deposits
        c3 = StatCard(kpi_container, title="Total Deposits", value="$0.00", subtext="Cumulative deposit volume", icon="📥", accent_color=Theme.ACCENT_CYAN)
        c3.grid(row=0, column=2, padx=6, pady=6, sticky="ew")
        self.stat_cards["deposits"] = c3

        # Card 4: Loan Exposure
        c4 = StatCard(kpi_container, title="Loan Exposure", value="$0.00", subtext="Total active principal", icon="💼", accent_color=Theme.WARNING)
        c4.grid(row=0, column=3, padx=6, pady=6, sticky="ew")
        self.stat_cards["loans"] = c4

    def _build_charts_row(self):
        charts_container = ctk.CTkFrame(self, fg_color="transparent")
        charts_container.pack(fill="x", padx=20, pady=(0, 16))

        charts_container.grid_columnconfigure(0, weight=6)
        charts_container.grid_columnconfigure(1, weight=4)

        # Chart 1: Monthly Transaction Activity
        self.chart_activity = ChartFrame(charts_container, title="Transaction Activity (Volume Trend)", height=320)
        self.chart_activity.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")

        # Chart 2: Account Distribution
        self.chart_distribution = ChartFrame(charts_container, title="Account Balances by Product", height=320)
        self.chart_distribution.grid(row=0, column=1, padx=6, pady=6, sticky="nsew")

    def _build_recent_transactions(self):
        table_container = ctk.CTkFrame(self, fg_color="transparent")
        table_container.pack(fill="both", expand=True, padx=26, pady=(0, 24))

        title_lbl = ctk.CTkLabel(
            table_container,
            text="RECENT FINANCIAL TRANSACTIONS",
            font=Theme.font_section(),
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
        )
        title_lbl.pack(fill="x", pady=(0, 8))

        columns = ["Reference No", "Account", "Type", "Amount", "Balance", "Date"]
        col_widths = [140, 110, 110, 100, 100, 130]
        self.recent_table = DataTable(table_container, columns=columns, col_widths=col_widths, searchable=False)
        self.recent_table.pack(fill="both", expand=True)

    def refresh_data(self):
        """Fetch updated statistics and replot charts."""
        kpis = report_service.get_kpi_summary()

        self.stat_cards["customers"].update_value(str(kpis["total_customers"]))
        self.stat_cards["accounts"].update_value(str(kpis["active_accounts"]))
        self.stat_cards["deposits"].update_value(format_currency(kpis["total_deposits"]))
        self.stat_cards["loans"].update_value(format_currency(kpis["total_loans_outstanding"]))

        # Render Monthly Activity Chart
        self._render_monthly_chart()

        # Render Distribution Chart
        self._render_distribution_chart()

        # Render Recent Transactions Table
        recent_txns = transaction_service.search_transactions(limit=8)
        table_rows = [
            {
                "Reference No": tx.reference_no,
                "Account": tx.account.account_number if tx.account else "N/A",
                "Type": tx.transaction_type,
                "Amount": format_currency(tx.amount),
                "Balance": format_currency(tx.new_balance),
                "Date": tx.created_at.strftime("%Y-%m-%d %H:%M") if tx.created_at else "N/A",
                "status": tx.status,
            }
            for tx in recent_txns
        ]
        self.recent_table.set_data(
            table_rows,
            key_fields=["Reference No", "Account", "Type", "Amount", "Balance", "Date"],
        )

    def _render_monthly_chart(self):
        df = report_service.get_monthly_transaction_stats(months=6)

        fig, ax = plt.subplots(figsize=(6, 3), dpi=90)
        fig.patch.set_facecolor(Theme.SURFACE_CARD)
        ax.set_facecolor(Theme.SURFACE_NAV)

        if not df.empty and "Month" in df.columns:
            months = df["Month"]
            x = range(len(months))
            width = 0.35

            dep_vals = df["Deposits"] if "Deposits" in df.columns else [0] * len(months)
            with_vals = df["Withdrawals"] if "Withdrawals" in df.columns else [0] * len(months)

            ax.bar([i - width/2 for i in x], dep_vals, width, label="Deposits", color=Theme.ACCENT_CYAN)
            ax.bar([i + width/2 for i in x], with_vals, width, label="Withdrawals", color=Theme.DANGER)

            ax.set_xticks(x)
            ax.set_xticklabels(months, color=Theme.TEXT_SECONDARY, fontsize=8)
        else:
            ax.text(0.5, 0.5, "No transaction history recorded", color=Theme.TEXT_MUTED, ha="center")

        ax.tick_params(colors=Theme.TEXT_SECONDARY, labelsize=8)
        ax.spines["bottom"].set_color(Theme.BORDER)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(Theme.BORDER)
        ax.grid(axis="y", color=Theme.BORDER, linestyle="--", alpha=0.5)
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(facecolor=Theme.SURFACE_CARD, edgecolor=Theme.BORDER, labelcolor=Theme.TEXT_PRIMARY, fontsize=8)

        plt.tight_layout()
        self.chart_activity.render_figure(fig)

    def _render_distribution_chart(self):
        df = report_service.get_account_type_distribution()

        fig, ax = plt.subplots(figsize=(4, 3), dpi=90)
        fig.patch.set_facecolor(Theme.SURFACE_CARD)
        ax.set_facecolor(Theme.SURFACE_NAV)

        if not df.empty and df["Total Balance"].sum() > 0:
            labels = df["Account Type"].tolist()
            sizes = df["Total Balance"].tolist()
            colors = [Theme.ACCENT_CYAN, Theme.SUCCESS, Theme.WARNING]

            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=None,
                autopct="%1.1f%%",
                startangle=140,
                colors=colors[:len(sizes)],
                textprops=dict(color=Theme.TEXT_PRIMARY, fontsize=8, weight="bold"),
                wedgeprops=dict(width=0.4, edgecolor=Theme.SURFACE_CARD),
            )
            ax.legend(
                wedges,
                labels,
                loc="lower center",
                bbox_to_anchor=(0.5, -0.15),
                ncol=1,
                facecolor=Theme.SURFACE_CARD,
                edgecolor=Theme.BORDER,
                labelcolor=Theme.TEXT_PRIMARY,
                fontsize=7,
            )
        else:
            ax.text(0.5, 0.5, "No active accounts balance", color=Theme.TEXT_MUTED, ha="center")

        plt.tight_layout()
        self.chart_distribution.render_figure(fig)
