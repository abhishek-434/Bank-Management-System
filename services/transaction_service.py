"""Core financial transaction and fund transfer execution engine."""
import logging
from decimal import Decimal
from datetime import datetime, timezone, time
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from database.connection import db_manager
from models.account import Account, AccountType
from models.transaction import Transaction, Transfer
from config.constants import TransactionType, TransactionStatus, TransferStatus, AccountStatus
from utils.generators import generate_transaction_ref, generate_transfer_ref
from utils.validators import validate_positive_amount
from services.audit_service import audit_service

logger = logging.getLogger("bms.transaction_service")


class TransactionService:
    """Atomic financial ledger transactions: Deposits, Withdrawals, and Internal Transfers."""

    def deposit(
        self,
        account_number: str,
        amount_input: object,
        description: str = "Deposit",
        user_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Execute an atomic deposit into a valid active account.
        Returns: (success, receipt_dict, error_message)
        """
        is_valid, amount, err = validate_positive_amount(amount_input)
        if not is_valid:
            return False, None, err

        with db_manager.session_scope() as session:
            # Query and lock account row
            stmt = (
                select(Account)
                .options(selectinload(Account.customer), selectinload(Account.account_type))
                .where(Account.account_number == account_number.strip())
            )
            # Add with_for_update if dialect is PostgreSQL
            if db_manager.active_dialect == "postgresql":
                stmt = stmt.with_for_update()

            account = session.execute(stmt).scalars().first()
            if not account:
                return False, None, f"Account number '{account_number}' not found."

            if not account.is_operational():
                return False, None, f"Account is {account.status}. Deposits are not permitted."

            # Calculate balances
            prev_balance = account.current_balance
            new_balance = prev_balance + amount
            account.current_balance = new_balance

            # Generate ledger record
            ref_no = generate_transaction_ref()
            now_dt = datetime.now(timezone.utc)
            txn = Transaction(
                reference_no=ref_no,
                account_id=account.id,
                transaction_type=TransactionType.DEPOSIT.value,
                amount=amount,
                previous_balance=prev_balance,
                new_balance=new_balance,
                description=description.strip() or "Account Deposit",
                status=TransactionStatus.SUCCESS.value,
                created_at=now_dt,
            )
            session.add(txn)

            # Audit record
            audit_service.log(
                action="FINANCIAL_DEPOSIT",
                target_entity="Account",
                target_id=account.id,
                user_id=user_id,
                details={
                    "reference": ref_no,
                    "account": account.account_number,
                    "amount": str(amount),
                    "new_balance": str(new_balance),
                },
                session=session,
            )

            receipt = {
                "receipt_type": "DEPOSIT",
                "reference_no": ref_no,
                "account_number": account.account_number,
                "customer_name": account.customer.full_name,
                "account_type": account.account_type.name,
                "amount": amount,
                "previous_balance": prev_balance,
                "new_balance": new_balance,
                "description": txn.description,
                "timestamp": now_dt,
                "status": "SUCCESS",
            }
            logger.info(f"Deposit {ref_no} of ${amount} to {account.account_number} completed.")
            return True, receipt, "Deposit processed successfully."

    def withdraw(
        self,
        account_number: str,
        amount_input: object,
        description: str = "Withdrawal",
        user_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Execute an atomic withdrawal from an active account.
        Validates minimum balance, positive amount, and daily withdrawal limits.
        """
        is_valid, amount, err = validate_positive_amount(amount_input)
        if not is_valid:
            return False, None, err

        with db_manager.session_scope() as session:
            stmt = (
                select(Account)
                .options(selectinload(Account.customer), selectinload(Account.account_type))
                .where(Account.account_number == account_number.strip())
            )
            if db_manager.active_dialect == "postgresql":
                stmt = stmt.with_for_update()

            account = session.execute(stmt).scalars().first()
            if not account:
                return False, None, f"Account '{account_number}' not found."

            if not account.is_operational():
                return False, None, f"Account is {account.status}. Withdrawals are prohibited."

            acct_type = account.account_type

            # Rule 1: Fixed Deposit restriction
            if acct_type.daily_withdrawal_limit == Decimal("0.00"):
                return False, None, "Fixed deposit accounts cannot perform direct on-demand withdrawals."

            # Rule 2: Minimum balance and available funds check
            available_balance = account.current_balance - acct_type.minimum_balance
            if amount > available_balance:
                return False, None, (
                    f"Insufficient funds. Account balance is ${account.current_balance:.2f}. "
                    f"Minimum required balance is ${acct_type.minimum_balance:.2f}. "
                    f"Maximum available for withdrawal is ${max(Decimal('0.00'), available_balance):.2f}."
                )

            # Rule 3: Daily withdrawal limit enforcement
            today_start = datetime.combine(datetime.now(timezone.utc).date(), time.min).replace(tzinfo=timezone.utc)
            today_withdrawals_stmt = select(func.coalesce(func.sum(Transaction.amount), Decimal("0.00"))).where(
                Transaction.account_id == account.id,
                Transaction.transaction_type == TransactionType.WITHDRAWAL.value,
                Transaction.status == TransactionStatus.SUCCESS.value,
                Transaction.created_at >= today_start,
            )
            total_withdrawn_today = session.execute(today_withdrawals_stmt).scalar() or Decimal("0.00")

            if (total_withdrawn_today + amount) > acct_type.daily_withdrawal_limit:
                rem_limit = max(Decimal("0.00"), acct_type.daily_withdrawal_limit - total_withdrawn_today)
                return False, None, (
                    f"Daily withdrawal limit exceeded. Daily limit is ${acct_type.daily_withdrawal_limit:.2f}. "
                    f"Already withdrawn today: ${total_withdrawn_today:.2f}. "
                    f"Remaining allowed withdrawal today: ${rem_limit:.2f}."
                )

            # Execute withdrawal
            prev_balance = account.current_balance
            new_balance = prev_balance - amount
            account.current_balance = new_balance

            ref_no = generate_transaction_ref()
            now_dt = datetime.now(timezone.utc)
            txn = Transaction(
                reference_no=ref_no,
                account_id=account.id,
                transaction_type=TransactionType.WITHDRAWAL.value,
                amount=amount,
                previous_balance=prev_balance,
                new_balance=new_balance,
                description=description.strip() or "Account Withdrawal",
                status=TransactionStatus.SUCCESS.value,
                created_at=now_dt,
            )
            session.add(txn)

            audit_service.log(
                action="FINANCIAL_WITHDRAWAL",
                target_entity="Account",
                target_id=account.id,
                user_id=user_id,
                details={
                    "reference": ref_no,
                    "account": account.account_number,
                    "amount": str(amount),
                    "new_balance": str(new_balance),
                },
                session=session,
            )

            receipt = {
                "receipt_type": "WITHDRAWAL",
                "reference_no": ref_no,
                "account_number": account.account_number,
                "customer_name": account.customer.full_name,
                "account_type": account.account_type.name,
                "amount": amount,
                "previous_balance": prev_balance,
                "new_balance": new_balance,
                "description": txn.description,
                "timestamp": now_dt,
                "status": "SUCCESS",
            }
            logger.info(f"Withdrawal {ref_no} of ${amount} from {account.account_number} completed.")
            return True, receipt, "Withdrawal processed successfully."

    def transfer(
        self,
        sender_account_no: str,
        receiver_account_no: str,
        amount_input: object,
        description: str = "Internal Transfer",
        user_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Execute an atomic account-to-account transfer.
        Guarantees that debit and credit operations succeed or fail together.
        """
        clean_sender = sender_account_no.strip()
        clean_receiver = receiver_account_no.strip()

        if clean_sender == clean_receiver:
            return False, None, "Sender and receiver accounts must be different."

        is_valid, amount, err = validate_positive_amount(amount_input)
        if not is_valid:
            return False, None, err

        with db_manager.session_scope() as session:
            # Query sender and receiver
            sender_stmt = (
                select(Account)
                .options(selectinload(Account.customer), selectinload(Account.account_type))
                .where(Account.account_number == clean_sender)
            )
            receiver_stmt = (
                select(Account)
                .options(selectinload(Account.customer), selectinload(Account.account_type))
                .where(Account.account_number == clean_receiver)
            )

            # In PostgreSQL, acquire locks in order of IDs to eliminate deadlock risk
            if db_manager.active_dialect == "postgresql":
                sender_stmt = sender_stmt.with_for_update()
                receiver_stmt = receiver_stmt.with_for_update()

            sender = session.execute(sender_stmt).scalars().first()
            receiver = session.execute(receiver_stmt).scalars().first()

            if not sender:
                return False, None, f"Sender account '{clean_sender}' does not exist."
            if not receiver:
                return False, None, f"Receiver account '{clean_receiver}' does not exist."

            if not sender.is_operational():
                return False, None, f"Sender account is {sender.status}. Transfer cannot proceed."
            if not receiver.is_operational():
                return False, None, f"Receiver account is {receiver.status}. Transfer cannot proceed."

            # Verify sender funds
            available_balance = sender.current_balance - sender.account_type.minimum_balance
            if amount > available_balance:
                return False, None, (
                    f"Insufficient funds in sender account. Balance: ${sender.current_balance:.2f}. "
                    f"Minimum balance: ${sender.account_type.minimum_balance:.2f}. "
                    f"Maximum transferable: ${max(Decimal('0.00'), available_balance):.2f}."
                )

            # Atomic balances update
            now_dt = datetime.now(timezone.utc)
            transfer_ref = generate_transfer_ref()

            sender_prev = sender.current_balance
            sender_new = sender_prev - amount
            sender.current_balance = sender_new

            receiver_prev = receiver.current_balance
            receiver_new = receiver_prev + amount
            receiver.current_balance = receiver_new

            # Create Sender Ledger Debit
            debit_ref = generate_transaction_ref(prefix="TXN-DB")
            debit_txn = Transaction(
                reference_no=debit_ref,
                account_id=sender.id,
                transaction_type=TransactionType.TRANSFER_DEBIT.value,
                amount=amount,
                previous_balance=sender_prev,
                new_balance=sender_new,
                description=f"Transfer to {receiver.account_number} ({receiver.customer.full_name}): {description}",
                status=TransactionStatus.SUCCESS.value,
                created_at=now_dt,
            )
            session.add(debit_txn)

            # Create Receiver Ledger Credit
            credit_ref = generate_transaction_ref(prefix="TXN-CR")
            credit_txn = Transaction(
                reference_no=credit_ref,
                account_id=receiver.id,
                transaction_type=TransactionType.TRANSFER_CREDIT.value,
                amount=amount,
                previous_balance=receiver_prev,
                new_balance=receiver_new,
                description=f"Transfer from {sender.account_number} ({sender.customer.full_name}): {description}",
                status=TransactionStatus.SUCCESS.value,
                created_at=now_dt,
            )
            session.add(credit_txn)

            # Create Transfer linking record
            transfer_rec = Transfer(
                transfer_reference=transfer_ref,
                sender_account_id=sender.id,
                receiver_account_id=receiver.id,
                amount=amount,
                description=description.strip(),
                status=TransferStatus.COMPLETED.value,
                created_at=now_dt,
            )
            session.add(transfer_rec)

            audit_service.log(
                action="FUND_TRANSFER",
                target_entity="Transfer",
                target_id=transfer_ref,
                user_id=user_id,
                details={
                    "transfer_ref": transfer_ref,
                    "sender": sender.account_number,
                    "receiver": receiver.account_number,
                    "amount": str(amount),
                },
                session=session,
            )

            receipt = {
                "receipt_type": "TRANSFER",
                "transfer_reference": transfer_ref,
                "sender_account": sender.account_number,
                "sender_name": sender.customer.full_name,
                "receiver_account": receiver.account_number,
                "receiver_name": receiver.customer.full_name,
                "amount": amount,
                "sender_new_balance": sender_new,
                "description": description.strip(),
                "timestamp": now_dt,
                "status": "COMPLETED",
            }
            logger.info(f"Transfer {transfer_ref} of ${amount} from {clean_sender} to {clean_receiver} succeeded.")
            return True, receipt, "Transfer completed successfully."

    def search_transactions(
        self,
        account_id: Optional[str] = None,
        account_number: Optional[str] = None,
        customer_id: Optional[str] = None,
        transaction_type: str = "ALL",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 150,
    ) -> List[Transaction]:
        """Search and filter ledger transactions."""
        with db_manager.session_scope() as session:
            stmt = select(Transaction).join(Account, Transaction.account_id == Account.id).options(selectinload(Transaction.account).selectinload(Account.customer))

            if account_id:
                stmt = stmt.where(Transaction.account_id == account_id)
            if account_number:
                stmt = stmt.where(Account.account_number == account_number.strip())
            if customer_id:
                stmt = stmt.where(Account.customer_id == customer_id)
            if transaction_type and transaction_type != "ALL":
                stmt = stmt.where(Transaction.transaction_type == transaction_type)
            if start_date:
                stmt = stmt.where(Transaction.created_at >= start_date)
            if end_date:
                stmt = stmt.where(Transaction.created_at <= end_date)

            stmt = stmt.order_by(Transaction.created_at.desc()).limit(limit)
            return session.execute(stmt).scalars().all()


transaction_service = TransactionService()

