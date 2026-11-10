"""Educational loan management, interest computation, and repayment engine."""
import logging
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.connection import db_manager
from models.loan import Loan, LoanRepayment
from models.customer import Customer
from models.account import Account
from models.transaction import Transaction
from config.constants import LoanStatus, CustomerStatus, AccountStatus, TransactionType, TransactionStatus
from utils.generators import generate_loan_ref, generate_transaction_ref
from utils.validators import validate_positive_amount
from services.audit_service import audit_service

logger = logging.getLogger("bms.loan_service")


class LoanService:
    """
    Manages loan applications, simplified educational interest computations,
    and loan repayment ledgers.
    """

    @staticmethod
    def calculate_loan_totals(principal: Decimal, annual_rate: Decimal, duration_months: int) -> Tuple[Decimal, Decimal]:
        """
        Compute total interest and total payable amount using standard simple interest:
        Interest = (P * R * M) / (100 * 12)
        Total Payable = P + Interest
        """
        p = Decimal(str(principal))
        r = Decimal(str(annual_rate))
        m = Decimal(str(duration_months))

        total_interest = (p * r * m) / (Decimal("100.00") * Decimal("12.00"))
        total_interest = total_interest.quantize(Decimal("0.01"))
        total_payable = p + total_interest
        return total_interest, total_payable

    def apply_for_loan(
        self,
        customer_id: str,
        principal_input: object,
        annual_rate: Decimal,
        duration_months: int,
        applied_by_user_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[Loan], str]:
        """Submit a new loan application subject to basic customer eligibility."""
        is_valid, principal, err = validate_positive_amount(principal_input)
        if not is_valid:
            return False, None, err

        if duration_months < 1 or duration_months > 360:
            return False, None, "Loan duration must be between 1 and 360 months."

        if annual_rate < Decimal("0.00") or annual_rate > Decimal("100.00"):
            return False, None, "Annual interest rate must be between 0% and 100%."

        with db_manager.session_scope() as session:
            customer = session.get(Customer, customer_id)
            if not customer:
                return False, None, "Customer does not exist."

            if customer.status != CustomerStatus.ACTIVE.value:
                return False, None, f"Customer is {customer.status}. Loan application denied."

            # Check for active accounts
            active_account = session.execute(
                select(Account).where(
                    Account.customer_id == customer_id,
                    Account.status == AccountStatus.ACTIVE.value,
                )
            ).scalars().first()
            if not active_account:
                return False, None, "Customer must have at least one active bank account to apply for a loan."

            total_interest, total_payable = self.calculate_loan_totals(principal, annual_rate, duration_months)
            loan_ref = generate_loan_ref()

            loan = Loan(
                loan_reference=loan_ref,
                customer_id=customer_id,
                principal_amount=principal,
                interest_rate=annual_rate,
                duration_months=duration_months,
                total_payable=total_payable,
                outstanding_balance=total_payable,
                status=LoanStatus.APPLIED.value,
                applied_at=datetime.now(timezone.utc),
            )
            session.add(loan)
            session.flush()

            audit_service.log(
                action="LOAN_APPLIED",
                target_entity="Loan",
                target_id=loan.id,
                user_id=applied_by_user_id,
                details={
                    "loan_ref": loan.loan_reference,
                    "customer_id": customer_id,
                    "principal": str(principal),
                    "total_payable": str(total_payable),
                },
                session=session,
            )
            return True, loan, f"Loan application {loan.loan_reference} submitted successfully."

    def review_loan(
        self,
        loan_id: str,
        approve: bool,
        reviewed_by_user_id: Optional[str] = None,
        disburse_account_number: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Approve or reject a loan application. If approved and account provided, disburses funds."""
        with db_manager.session_scope() as session:
            loan = session.get(Loan, loan_id)
            if not loan:
                return False, "Loan not found."

            if loan.status != LoanStatus.APPLIED.value:
                return False, f"Loan is already {loan.status}. Cannot review."

            now_dt = datetime.now(timezone.utc)
            if not approve:
                loan.status = LoanStatus.REJECTED.value
                audit_service.log(
                    action="LOAN_REJECTED",
                    target_entity="Loan",
                    target_id=loan.id,
                    user_id=reviewed_by_user_id,
                    details={"loan_ref": loan.loan_reference},
                    session=session,
                )
                return True, f"Loan {loan.loan_reference} has been rejected."

            loan.status = LoanStatus.APPROVED.value
            loan.approved_at = now_dt

            # Optional disbursement
            if disburse_account_number:
                account = session.execute(
                    select(Account).where(
                        Account.account_number == disburse_account_number.strip(),
                        Account.customer_id == loan.customer_id,
                    )
                ).scalars().first()

                if not account:
                    return False, f"Account '{disburse_account_number}' not found for customer."

                if not account.is_operational():
                    return False, f"Account '{disburse_account_number}' is {account.status}. Cannot disburse."

                # Disburse funds
                prev_balance = account.current_balance
                new_balance = prev_balance + loan.principal_amount
                account.current_balance = new_balance
                loan.status = LoanStatus.DISBURSED.value

                ref_no = generate_transaction_ref(prefix="TXN-LN")
                txn = Transaction(
                    reference_no=ref_no,
                    account_id=account.id,
                    transaction_type=TransactionType.LOAN_DISBURSEMENT.value,
                    amount=loan.principal_amount,
                    previous_balance=prev_balance,
                    new_balance=new_balance,
                    description=f"Disbursement for loan {loan.loan_reference}",
                    status=TransactionStatus.SUCCESS.value,
                    created_at=now_dt,
                )
                session.add(txn)

            audit_service.log(
                action="LOAN_APPROVED",
                target_entity="Loan",
                target_id=loan.id,
                user_id=reviewed_by_user_id,
                details={"loan_ref": loan.loan_reference, "status": loan.status},
                session=session,
            )
            return True, f"Loan {loan.loan_reference} approved (Status: {loan.status})."

    def repay_loan(
        self,
        loan_id: str,
        repayment_amount_input: object,
        deduct_from_account_no: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Make a repayment towards an active loan."""
        is_valid, amount, err = validate_positive_amount(repayment_amount_input)
        if not is_valid:
            return False, err

        with db_manager.session_scope() as session:
            loan = session.get(Loan, loan_id)
            if not loan:
                return False, "Loan record not found."

            if loan.status not in (LoanStatus.APPROVED.value, LoanStatus.DISBURSED.value):
                return False, f"Cannot accept payment. Loan status is {loan.status}."

            if amount > loan.outstanding_balance:
                return False, f"Payment (${amount:.2f}) exceeds outstanding balance of ${loan.outstanding_balance:.2f}."

            now_dt = datetime.now(timezone.utc)

            # Optional account deduction
            if deduct_from_account_no:
                account = session.execute(
                    select(Account).where(Account.account_number == deduct_from_account_no.strip())
                ).scalars().first()
                if not account:
                    return False, f"Account '{deduct_from_account_no}' not found."

                available = account.current_balance - account.account_type.minimum_balance
                if amount > available:
                    return False, f"Insufficient funds in account {deduct_from_account_no}. Available: ${available:.2f}."

                prev_balance = account.current_balance
                new_balance = prev_balance - amount
                account.current_balance = new_balance

                txn = Transaction(
                    reference_no=generate_transaction_ref(prefix="TXN-RP"),
                    account_id=account.id,
                    transaction_type=TransactionType.LOAN_REPAYMENT.value,
                    amount=amount,
                    previous_balance=prev_balance,
                    new_balance=new_balance,
                    description=f"Repayment for loan {loan.loan_reference}",
                    status=TransactionStatus.SUCCESS.value,
                    created_at=now_dt,
                )
                session.add(txn)

            # Repayment splits (pro-rata principal & interest)
            ratio = loan.principal_amount / loan.total_payable
            principal_part = (amount * ratio).quantize(Decimal("0.01"))
            interest_part = amount - principal_part
            new_outstanding = loan.outstanding_balance - amount
            loan.outstanding_balance = new_outstanding

            if new_outstanding == Decimal("0.00"):
                loan.status = LoanStatus.CLOSED.value

            repayment_rec = LoanRepayment(
                loan_id=loan.id,
                payment_reference=generate_transaction_ref(prefix="PAY"),
                amount=amount,
                principal_portion=principal_part,
                interest_portion=interest_part,
                balance_after_payment=new_outstanding,
                paid_at=now_dt,
            )
            session.add(repayment_rec)

            audit_service.log(
                action="LOAN_REPAYMENT",
                target_entity="Loan",
                target_id=loan.id,
                user_id=user_id,
                details={
                    "payment_ref": repayment_rec.payment_reference,
                    "amount": str(amount),
                    "remaining_balance": str(new_outstanding),
                },
                session=session,
            )
            msg = f"Repayment of ${amount:,.2f} processed. Remaining balance: ${new_outstanding:,.2f}."
            if loan.status == LoanStatus.CLOSED.value:
                msg += " Loan has been completely paid off and marked CLOSED!"
            return True, msg

    def list_loans(
        self,
        customer_id: Optional[str] = None,
        status_filter: str = "ALL",
    ) -> List[Loan]:
        """Retrieve loans matching customer and status filters."""
        with db_manager.session_scope() as session:
            stmt = select(Loan).options(selectinload(Loan.customer), selectinload(Loan.repayments))
            if customer_id:
                stmt = stmt.where(Loan.customer_id == customer_id)
            if status_filter and status_filter != "ALL":
                stmt = stmt.where(Loan.status == status_filter)

            stmt = stmt.order_by(Loan.applied_at.desc())
            return session.execute(stmt).scalars().all()


loan_service = LoanService()
