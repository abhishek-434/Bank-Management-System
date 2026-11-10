"""Reporting and financial analytics service powered by Pandas."""
import logging
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
from sqlalchemy import select, func
from database.connection import db_manager
from models.customer import Customer
from models.account import Account, AccountType
from models.transaction import Transaction, Transfer
from models.loan import Loan
from config.constants import AccountStatus, TransactionStatus, TransactionType, LoanStatus, TransferStatus
from config.settings import settings

logger = logging.getLogger("bms.report_service")


class ReportService:
    """Aggregates metrics and generates analytical reports."""

    def get_kpi_summary(self) -> Dict[str, Any]:
        """Fetch high-level administrative KPI metrics."""
        with db_manager.session_scope() as session:
            total_customers = session.execute(select(func.count(Customer.id))).scalar() or 0
            active_accounts = session.execute(
                select(func.count(Account.id)).where(Account.status == AccountStatus.ACTIVE.value)
            ).scalar() or 0

            total_deposits = session.execute(
                select(func.coalesce(func.sum(Transaction.amount), Decimal("0.00"))).where(
                    Transaction.transaction_type == TransactionType.DEPOSIT.value,
                    Transaction.status == TransactionStatus.SUCCESS.value,
                )
            ).scalar() or Decimal("0.00")

            total_withdrawals = session.execute(
                select(func.coalesce(func.sum(Transaction.amount), Decimal("0.00"))).where(
                    Transaction.transaction_type == TransactionType.WITHDRAWAL.value,
                    Transaction.status == TransactionStatus.SUCCESS.value,
                )
            ).scalar() or Decimal("0.00")

            total_transfer_volume = session.execute(
                select(func.coalesce(func.sum(Transfer.amount), Decimal("0.00"))).where(
                    Transfer.status == TransferStatus.COMPLETED.value
                )
            ).scalar() or Decimal("0.00")

            total_loans_count = session.execute(select(func.count(Loan.id))).scalar() or 0
            total_loans_outstanding = session.execute(
                select(func.coalesce(func.sum(Loan.outstanding_balance), Decimal("0.00"))).where(
                    Loan.status.in_([LoanStatus.APPROVED.value, LoanStatus.DISBURSED.value])
                )
            ).scalar() or Decimal("0.00")

            total_bank_balance = session.execute(
                select(func.coalesce(func.sum(Account.current_balance), Decimal("0.00"))).where(
                    Account.status != AccountStatus.CLOSED.value
                )
            ).scalar() or Decimal("0.00")

            return {
                "total_customers": total_customers,
                "active_accounts": active_accounts,
                "total_deposits": Decimal(str(total_deposits)),
                "total_withdrawals": Decimal(str(total_withdrawals)),
                "total_transfer_volume": Decimal(str(total_transfer_volume)),
                "total_loans_count": total_loans_count,
                "total_loans_outstanding": Decimal(str(total_loans_outstanding)),
                "total_bank_balance": Decimal(str(total_bank_balance)),
            }

    def get_monthly_transaction_stats(self, months: int = 6) -> pd.DataFrame:
        """Aggregate monthly deposits, withdrawals, and transfers over recent months."""
        with db_manager.session_scope() as session:
            stmt = select(
                Transaction.created_at,
                Transaction.transaction_type,
                Transaction.amount,
            ).where(Transaction.status == TransactionStatus.SUCCESS.value)

            records = session.execute(stmt).all()
            if not records:
                # Return empty formatted DataFrame
                return pd.DataFrame(columns=["Month", "Deposits", "Withdrawals", "Transfers"])

            data = [
                {
                    "created_at": r[0],
                    "type": r[1],
                    "amount": float(r[2]),
                }
                for r in records
            ]
            df = pd.DataFrame(data)
            df["Month"] = pd.to_datetime(df["created_at"]).dt.strftime("%Y-%m")

            pivot = df.pivot_table(
                index="Month",
                columns="type",
                values="amount",
                aggfunc="sum",
                fill_value=0.0,
            ).reset_index()

            # Ensure expected columns exist
            for col in ["DEPOSIT", "WITHDRAWAL", "TRANSFER_DEBIT"]:
                if col not in pivot.columns:
                    pivot[col] = 0.0

            pivot.rename(
                columns={
                    "DEPOSIT": "Deposits",
                    "WITHDRAWAL": "Withdrawals",
                    "TRANSFER_DEBIT": "Transfers",
                },
                inplace=True,
            )

            # Sort and take latest N months
            pivot = pivot.sort_values(by="Month").tail(months)
            return pivot

    def get_account_type_distribution(self) -> pd.DataFrame:
        """Get account counts and total balances by account type."""
        with db_manager.session_scope() as session:
            stmt = (
                select(
                    AccountType.name,
                    func.count(Account.id).label("count"),
                    func.coalesce(func.sum(Account.current_balance), Decimal("0.00")).label("balance"),
                )
                .join(Account, Account.account_type_id == AccountType.id, isouter=True)
                .group_by(AccountType.name)
            )
            rows = session.execute(stmt).all()
            data = [{"Account Type": r[0], "Count": r[1], "Total Balance": float(r[2])} for r in rows]
            return pd.DataFrame(data)

    def export_transactions_to_csv(self, file_path: str, account_number: Optional[str] = None) -> str:
        """Export ledger transactions to a CSV file."""
        with db_manager.session_scope() as session:
            stmt = select(
                Transaction.reference_no,
                Account.account_number,
                Transaction.transaction_type,
                Transaction.amount,
                Transaction.previous_balance,
                Transaction.new_balance,
                Transaction.status,
                Transaction.description,
                Transaction.created_at,
            ).join(Account, Transaction.account_id == Account.id)

            if account_number:
                stmt = stmt.where(Account.account_number == account_number.strip())

            stmt = stmt.order_by(Transaction.created_at.desc())
            rows = session.execute(stmt).all()

            data = [
                {
                    "Reference": r[0],
                    "Account Number": r[1],
                    "Type": r[2],
                    "Amount": float(r[3]),
                    "Previous Balance": float(r[4]),
                    "New Balance": float(r[5]),
                    "Status": r[6],
                    "Description": r[7],
                    "Timestamp (UTC)": r[8].strftime("%Y-%m-%d %H:%M:%S") if r[8] else "",
                }
                for r in rows
            ]
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False)
            return file_path


report_service = ReportService()

