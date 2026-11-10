"""Views package exporting all screen controllers."""
from ui.views.login_view import LoginView
from ui.views.admin_dashboard import AdminDashboardView
from ui.views.customer_mgmt_view import CustomerMgmtView
from ui.views.account_mgmt_view import AccountMgmtView
from ui.views.deposit_view import DepositView
from ui.views.withdrawal_view import WithdrawalView
from ui.views.transfer_view import TransferView
from ui.views.transaction_history import TransactionHistoryView
from ui.views.loan_mgmt_view import LoanMgmtView
from ui.views.reports_view import ReportsView
from ui.views.employee_mgmt_view import EmployeeMgmtView
from ui.views.audit_logs_view import AuditLogsView

__all__ = [
    "LoginView",
    "AdminDashboardView",
    "CustomerMgmtView",
    "AccountMgmtView",
    "DepositView",
    "WithdrawalView",
    "TransferView",
    "TransactionHistoryView",
    "LoanMgmtView",
    "ReportsView",
    "EmployeeMgmtView",
    "AuditLogsView",
]

