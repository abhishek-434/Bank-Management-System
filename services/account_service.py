"""Bank account management service."""
import logging
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from database.connection import db_manager
from models.account import Account, AccountType
from models.customer import Customer
from models.transaction import Transaction
from models.loan import Loan
from config.constants import AccountStatus, CustomerStatus, TransactionType, TransactionStatus, LoanStatus
from utils.generators import generate_account_number, generate_transaction_ref
from services.audit_service import audit_service

logger = logging.getLogger("bms.account_service")


class AccountService:
    """Handles bank account creation, queries, statement lookups, and lifecycle."""

    def get_account_types(self) -> List[AccountType]:
        """Fetch all available account types."""
        with db_manager.session_scope() as session:
            return session.execute(select(AccountType)).scalars().all()

    def open_account(
        self,
        customer_id: str,
        account_type_code: str,
        initial_deposit: Decimal,
        currency: str = "USD",
        created_by_user_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[Account], str]:
        """
        Open a new bank account with initial deposit verification.
        Creates account and records initial ledger entry.
        """
        if not isinstance(initial_deposit, Decimal):
            initial_deposit = Decimal(str(initial_deposit))

        with db_manager.session_scope() as session:
            customer = session.get(Customer, customer_id)
            if not customer:
                return False, None, "Customer does not exist."

            if customer.status != CustomerStatus.ACTIVE.value:
                return False, None, f"Cannot open account: Customer is {customer.status}."

            acct_type = session.execute(
                select(AccountType).where(AccountType.code == account_type_code)
            ).scalars().first()
            if not acct_type:
                return False, None, f"Unknown account type: {account_type_code}"

            if initial_deposit < acct_type.minimum_balance:
                return False, None, (
                    f"Initial deposit (${initial_deposit:.2f}) is below the required "
                    f"minimum balance of ${acct_type.minimum_balance:.2f}."
                )

            # Generate unique account number
            for _ in range(10):
                candidate_no = generate_account_number()
                exists = session.execute(
                    select(Account).where(Account.account_number == candidate_no)
                ).scalars().first()
                if not exists:
                    account_number = candidate_no
                    break
            else:
                return False, None, "Failed to generate unique account number. Please try again."

            account = Account(
                account_number=account_number,
                customer_id=customer_id,
                account_type_id=acct_type.id,
                current_balance=initial_deposit,
                currency=currency,
                status=AccountStatus.ACTIVE.value,
                opened_at=datetime.now(timezone.utc),
            )
            session.add(account)
            session.flush()

            # Record initial deposit ledger transaction if > 0
            if initial_deposit > Decimal("0.00"):
                initial_txn = Transaction(
                    reference_no=generate_transaction_ref(),
                    account_id=account.id,
                    transaction_type=TransactionType.DEPOSIT.value,
                    amount=initial_deposit,
                    previous_balance=Decimal("0.00"),
                    new_balance=initial_deposit,
                    description="Initial opening deposit",
                    status=TransactionStatus.SUCCESS.value,
                    created_at=datetime.now(timezone.utc),
                )
                session.add(initial_txn)

            audit_service.log(
                action="ACCOUNT_OPENED",
                target_entity="Account",
                target_id=account.id,
                user_id=created_by_user_id,
                details={
                    "account_number": account.account_number,
                    "customer_id": customer_id,
                    "type": acct_type.code,
                    "initial_deposit": str(initial_deposit),
                },
                session=session,
            )

            logger.info(f"Account {account.account_number} opened successfully for customer {customer_id}.")
            return True, account, f"Account {account.account_number} created successfully."

    def get_by_number(self, account_number: str) -> Optional[Account]:
        """Fetch account by account number including relations."""
        with db_manager.session_scope() as session:
            stmt = (
                select(Account)
                .options(selectinload(Account.customer), selectinload(Account.account_type))
                .where(Account.account_number == account_number.strip())
            )
            return session.execute(stmt).scalars().first()

    def get_by_id(self, account_id: str) -> Optional[Account]:
        """Fetch account by primary key ID."""
        with db_manager.session_scope() as session:
            stmt = (
                select(Account)
                .options(selectinload(Account.customer), selectinload(Account.account_type))
                .where(Account.id == account_id)
            )
            return session.execute(stmt).scalars().first()

    def list_by_customer(self, customer_id: str) -> List[Account]:
        """List all accounts for a specific customer."""
        with db_manager.session_scope() as session:
            stmt = (
                select(Account)
                .options(selectinload(Account.account_type))
                .where(Account.customer_id == customer_id)
                .order_by(Account.opened_at.desc())
            )
            return session.execute(stmt).scalars().all()

    def list_all_accounts(
        self,
        search_query: str = "",
        type_filter: str = "ALL",
        status_filter: str = "ALL",
        limit: int = 150,
    ) -> List[Account]:
        """Search and filter bank accounts across all customers."""
        with db_manager.session_scope() as session:
            stmt = (
                select(Account)
                .join(Customer, Account.customer_id == Customer.id)
                .join(AccountType, Account.account_type_id == AccountType.id)
                .options(selectinload(Account.customer), selectinload(Account.account_type))
            )

            if status_filter and status_filter != "ALL":
                stmt = stmt.where(Account.status == status_filter)

            if type_filter and type_filter != "ALL":
                stmt = stmt.where(AccountType.code == type_filter)

            if search_query:
                q = f"%{search_query.strip()}%"
                stmt = stmt.where(
                    or_(
                        Account.account_number.ilike(q),
                        Customer.first_name.ilike(q),
                        Customer.last_name.ilike(q),
                        Customer.customer_code.ilike(q),
                    )
                )

            stmt = stmt.order_by(Account.opened_at.desc()).limit(limit)
            return session.execute(stmt).scalars().all()

    def set_status(
        self,
        account_id: str,
        new_status: str,
        user_id: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Change account status.
        Enforces closing eligibility rules:
        - Balance must be zero.
        - No outstanding active loans.
        """
        valid_statuses = [s.value for s in AccountStatus]
        if new_status not in valid_statuses:
            return False, f"Invalid account status. Valid options: {', '.join(valid_statuses)}"

        with db_manager.session_scope() as session:
            account = session.get(Account, account_id)
            if not account:
                return False, "Account not found."

            if account.status == new_status:
                return True, f"Account is already {new_status}."

            if new_status == AccountStatus.CLOSED.value:
                # Eligibility check 1: zero balance
                if account.current_balance != Decimal("0.00"):
                    return False, (
                        f"Cannot close account. Balance must be $0.00. "
                        f"Current balance is ${account.current_balance:.2f}."
                    )

                # Eligibility check 2: active loans for this customer
                active_loans = session.execute(
                    select(Loan).where(
                        Loan.customer_id == account.customer_id,
                        Loan.status.in_([LoanStatus.APPROVED.value, LoanStatus.DISBURSED.value]),
                        Loan.outstanding_balance > Decimal("0.00"),
                    )
                ).scalars().all()
                if active_loans:
                    return False, "Cannot close account: Customer has active outstanding loans."

                account.closed_at = datetime.now(timezone.utc)

            old_status = account.status
            account.status = new_status

            audit_service.log(
                action="ACCOUNT_STATUS_CHANGED",
                target_entity="Account",
                target_id=account.id,
                user_id=user_id,
                details={
                    "account_number": account.account_number,
                    "old_status": old_status,
                    "new_status": new_status,
                },
                session=session,
            )
            return True, f"Account {account.account_number} status updated to {new_status}."


account_service = AccountService()

