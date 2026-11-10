"""Rich synthetic demonstration data generator."""
import logging
from decimal import Decimal
from datetime import datetime, timezone, timedelta, date
from sqlalchemy import select
from database.connection import db_manager
from database.migrations.init_db import init_database
from models.user import User
from models.customer import Customer
from models.employee import Employee
from models.account import Account, AccountType
from models.transaction import Transaction, Transfer
from models.loan import Loan, LoanRepayment
from models.audit import AuditLog
from config.constants import (
    UserRole,
    CustomerStatus,
    EmployeeStatus,
    AccountStatus,
    AccountTypeEnum,
    TransactionType,
    TransactionStatus,
    TransferStatus,
    LoanStatus,
)
from services.auth_service import auth_service
from services.loan_service import loan_service
from utils.generators import (
    generate_account_number,
    generate_transaction_ref,
    generate_transfer_ref,
    generate_loan_ref,
    generate_customer_code,
    generate_employee_code,
)

logger = logging.getLogger("bms.seed_data")


def seed_demo_data(engine=None) -> None:
    """Populate database with synthetic demonstration data."""
    init_database(engine)

    with db_manager.session_scope() as session:
        # Check if already seeded
        existing_admin = session.execute(
            select(User).where(User.username == "admin")
        ).scalars().first()
        if existing_admin:
            logger.info("Database is already seeded with demonstration data.")
            return

        logger.info("Seeding demonstration data...")
        now = datetime.now(timezone.utc)

        # 1. Administrator
        admin_user = User(
            username="admin",
            password_hash=auth_service.hash_password("Admin@123"),
            role=UserRole.ADMIN.value,
            is_active=True,
            last_login=now,
        )
        session.add(admin_user)
        session.flush()

        admin_emp = Employee(
            user_id=admin_user.id,
            employee_code=generate_employee_code(prefix="ADM"),
            first_name="Alexander",
            last_name="Vance",
            department="Executive Management",
            designation="Chief Systems Architect",
            email="admin@demo-bank.org",
            phone="+1-555-0100",
            status=EmployeeStatus.ACTIVE.value,
        )
        session.add(admin_emp)

        # 2. Employees
        emp1_user = User(
            username="employee1",
            password_hash=auth_service.hash_password("Employee@123"),
            role=UserRole.EMPLOYEE.value,
            is_active=True,
            last_login=now - timedelta(hours=2),
        )
        session.add(emp1_user)
        session.flush()

        emp1 = Employee(
            user_id=emp1_user.id,
            employee_code=generate_employee_code(),
            first_name="Sarah",
            last_name="Jenkins",
            department="Branch Operations",
            designation="Senior Banking Officer",
            email="sarah.jenkins@demo-bank.org",
            phone="+1-555-0101",
            status=EmployeeStatus.ACTIVE.value,
        )
        session.add(emp1)

        emp2_user = User(
            username="employee2",
            password_hash=auth_service.hash_password("Employee@123"),
            role=UserRole.EMPLOYEE.value,
            is_active=True,
        )
        session.add(emp2_user)
        session.flush()

        emp2 = Employee(
            user_id=emp2_user.id,
            employee_code=generate_employee_code(),
            first_name="David",
            last_name="Ross",
            department="Credit & Lending",
            designation="Loan Specialist",
            email="david.ross@demo-bank.org",
            phone="+1-555-0102",
            status=EmployeeStatus.ACTIVE.value,
        )
        session.add(emp2)

        # Retrieve Account Types
        savings_type = session.execute(
            select(AccountType).where(AccountType.code == AccountTypeEnum.SAVINGS.value)
        ).scalars().first()
        current_type = session.execute(
            select(AccountType).where(AccountType.code == AccountTypeEnum.CURRENT.value)
        ).scalars().first()
        fd_type = session.execute(
            select(AccountType).where(AccountType.code == AccountTypeEnum.FIXED_DEPOSIT.value)
        ).scalars().first()

        # 3. Customer 1: Eleanor Sterling
        c1_user = User(
            username="customer1",
            password_hash=auth_service.hash_password("Customer@123"),
            role=UserRole.CUSTOMER.value,
            is_active=True,
            last_login=now - timedelta(days=1),
        )
        session.add(c1_user)
        session.flush()

        cust1 = Customer(
            user_id=c1_user.id,
            customer_code="CUST-104921",
            first_name="Eleanor",
            last_name="Sterling",
            date_of_birth=date(1988, 5, 14),
            email="eleanor.sterling@demo-bank.org",
            phone="+1-555-0201",
            address="742 Evergreen Terrace, Springfield, IL",
            govt_id_masked="ID-***-8491",
            status=CustomerStatus.ACTIVE.value,
        )
        session.add(cust1)
        session.flush()

        acct1 = Account(
            account_number="1008472910",
            customer_id=cust1.id,
            account_type_id=savings_type.id,
            current_balance=Decimal("25450.00"),
            currency="USD",
            status=AccountStatus.ACTIVE.value,
            opened_at=now - timedelta(days=60),
        )
        session.add(acct1)

        acct1_fd = Account(
            account_number="1009182341",
            customer_id=cust1.id,
            account_type_id=fd_type.id,
            current_balance=Decimal("50000.00"),
            currency="USD",
            status=AccountStatus.ACTIVE.value,
            opened_at=now - timedelta(days=45),
        )
        session.add(acct1_fd)

        # 4. Customer 2: Marcus Thorne
        c2_user = User(
            username="customer2",
            password_hash=auth_service.hash_password("Customer@123"),
            role=UserRole.CUSTOMER.value,
            is_active=True,
        )
        session.add(c2_user)
        session.flush()

        cust2 = Customer(
            user_id=c2_user.id,
            customer_code="CUST-208394",
            first_name="Marcus",
            last_name="Thorne",
            date_of_birth=date(1992, 11, 23),
            email="marcus.thorne@demo-bank.org",
            phone="+1-555-0202",
            address="1204 Elm Street, Riverdale, NY",
            govt_id_masked="ID-***-3928",
            status=CustomerStatus.ACTIVE.value,
        )
        session.add(cust2)
        session.flush()

        acct2 = Account(
            account_number="1003928172",
            customer_id=cust2.id,
            account_type_id=current_type.id,
            current_balance=Decimal("12800.00"),
            currency="USD",
            status=AccountStatus.ACTIVE.value,
            opened_at=now - timedelta(days=35),
        )
        session.add(acct2)

        # 5. Customer 3: Chloe Bennett
        c3_user = User(
            username="customer3",
            password_hash=auth_service.hash_password("Customer@123"),
            role=UserRole.CUSTOMER.value,
            is_active=True,
        )
        session.add(c3_user)
        session.flush()

        cust3 = Customer(
            user_id=c3_user.id,
            customer_code="CUST-309182",
            first_name="Chloe",
            last_name="Bennett",
            date_of_birth=date(1995, 3, 8),
            email="chloe.bennett@demo-bank.org",
            phone="+1-555-0203",
            address="88 Crescent Avenue, Boston, MA",
            govt_id_masked="ID-***-1142",
            status=CustomerStatus.ACTIVE.value,
        )
        session.add(cust3)
        session.flush()

        acct3 = Account(
            account_number="1005829143",
            customer_id=cust3.id,
            account_type_id=savings_type.id,
            current_balance=Decimal("8250.00"),
            currency="USD",
            status=AccountStatus.ACTIVE.value,
            opened_at=now - timedelta(days=20),
        )
        session.add(acct3)
        session.flush()

        # 6. Historical Transactions
        # Eleanor savings opening deposit
        session.add(
            Transaction(
                reference_no="TXN-20261010-001001",
                account_id=acct1.id,
                transaction_type=TransactionType.DEPOSIT.value,
                amount=Decimal("20000.00"),
                previous_balance=Decimal("0.00"),
                new_balance=Decimal("20000.00"),
                description="Initial Account Opening Deposit",
                status=TransactionStatus.SUCCESS.value,
                created_at=now - timedelta(days=60),
            )
        )
        # Eleanor FD opening
        session.add(
            Transaction(
                reference_no="TXN-20261025-001002",
                account_id=acct1_fd.id,
                transaction_type=TransactionType.DEPOSIT.value,
                amount=Decimal("50000.00"),
                previous_balance=Decimal("0.00"),
                new_balance=Decimal("50000.00"),
                description="Fixed Deposit Placement",
                status=TransactionStatus.SUCCESS.value,
                created_at=now - timedelta(days=45),
            )
        )
        # Marcus current account deposit
        session.add(
            Transaction(
                reference_no="TXN-20261101-002001",
                account_id=acct2.id,
                transaction_type=TransactionType.DEPOSIT.value,
                amount=Decimal("15000.00"),
                previous_balance=Decimal("0.00"),
                new_balance=Decimal("15000.00"),
                description="Commercial deposit",
                status=TransactionStatus.SUCCESS.value,
                created_at=now - timedelta(days=35),
            )
        )
        # Marcus withdrawal
        session.add(
            Transaction(
                reference_no="TXN-20261105-002002",
                account_id=acct2.id,
                transaction_type=TransactionType.WITHDRAWAL.value,
                amount=Decimal("1200.00"),
                previous_balance=Decimal("15000.00"),
                new_balance=Decimal("13800.00"),
                description="ATM Cash Withdrawal",
                status=TransactionStatus.SUCCESS.value,
                created_at=now - timedelta(days=25),
            )
        )
        # Transfer from Eleanor to Marcus ($1,000)
        session.add(
            Transaction(
                reference_no="TXN-20261110-003001",
                account_id=acct1.id,
                transaction_type=TransactionType.TRANSFER_DEBIT.value,
                amount=Decimal("1000.00"),
                previous_balance=Decimal("20000.00"),
                new_balance=Decimal("19000.00"),
                description=f"Transfer to {acct2.account_number} (Marcus Thorne): Consulting invoice",
                status=TransactionStatus.SUCCESS.value,
                created_at=now - timedelta(days=15),
            )
        )
        session.add(
            Transaction(
                reference_no="TXN-20261110-003002",
                account_id=acct2.id,
                transaction_type=TransactionType.TRANSFER_CREDIT.value,
                amount=Decimal("1000.00"),
                previous_balance=Decimal("13800.00"),
                new_balance=Decimal("14800.00"),
                description=f"Transfer from {acct1.account_number} (Eleanor Sterling): Consulting invoice",
                status=TransactionStatus.SUCCESS.value,
                created_at=now - timedelta(days=15),
            )
        )
        session.add(
            Transfer(
                transfer_reference="TRF-20261110-009182",
                sender_account_id=acct1.id,
                receiver_account_id=acct2.id,
                amount=Decimal("1000.00"),
                description="Consulting invoice",
                status=TransferStatus.COMPLETED.value,
                created_at=now - timedelta(days=15),
            )
        )

        # Eleanor salary deposit ($6,450.00)
        session.add(
            Transaction(
                reference_no="TXN-20261115-004001",
                account_id=acct1.id,
                transaction_type=TransactionType.DEPOSIT.value,
                amount=Decimal("6450.00"),
                previous_balance=Decimal("19000.00"),
                new_balance=Decimal("25450.00"),
                description="Monthly Salary Deposit",
                status=TransactionStatus.SUCCESS.value,
                created_at=now - timedelta(days=5),
            )
        )

        # Marcus equipment withdrawal ($2,000.00)
        session.add(
            Transaction(
                reference_no="TXN-20261118-005001",
                account_id=acct2.id,
                transaction_type=TransactionType.WITHDRAWAL.value,
                amount=Decimal("2000.00"),
                previous_balance=Decimal("14800.00"),
                new_balance=Decimal("12800.00"),
                description="Office Equipment Purchase",
                status=TransactionStatus.SUCCESS.value,
                created_at=now - timedelta(days=2),
            )
        )

        # Chloe opening deposit ($8,250.00)
        session.add(
            Transaction(
                reference_no="TXN-20261120-006001",
                account_id=acct3.id,
                transaction_type=TransactionType.DEPOSIT.value,
                amount=Decimal("8250.00"),
                previous_balance=Decimal("0.00"),
                new_balance=Decimal("8250.00"),
                description="Initial Account Deposit",
                status=TransactionStatus.SUCCESS.value,
                created_at=now - timedelta(days=20),
            )
        )

        # 7. Loans
        # Eleanor: Approved & Disbursed Home Improvement Loan ($15,000 @ 5.5% for 24 months)
        loan1_interest, loan1_total = loan_service.calculate_loan_totals(Decimal("15000.00"), Decimal("5.50"), 24)
        loan1 = Loan(
            loan_reference="LN-202610-847291",
            customer_id=cust1.id,
            principal_amount=Decimal("15000.00"),
            interest_rate=Decimal("5.50"),
            duration_months=24,
            total_payable=loan1_total,
            outstanding_balance=loan1_total - Decimal("1390.00"),
            status=LoanStatus.DISBURSED.value,
            applied_at=now - timedelta(days=50),
            approved_at=now - timedelta(days=48),
        )
        session.add(loan1)
        session.flush()

        # Eleanor repayment 1 ($695.00)
        session.add(
            LoanRepayment(
                loan_id=loan1.id,
                payment_reference="PAY-202611-001",
                amount=Decimal("695.00"),
                principal_portion=Decimal("625.00"),
                interest_portion=Decimal("70.00"),
                balance_after_payment=loan1_total - Decimal("695.00"),
                paid_at=now - timedelta(days=30),
            )
        )
        # Eleanor repayment 2 ($695.00)
        session.add(
            LoanRepayment(
                loan_id=loan1.id,
                payment_reference="PAY-202611-002",
                amount=Decimal("695.00"),
                principal_portion=Decimal("625.00"),
                interest_portion=Decimal("70.00"),
                balance_after_payment=loan1_total - Decimal("1390.00"),
                paid_at=now - timedelta(days=2),
            )
        )

        # Marcus: Applied Loan ($5,000 @ 7.0% for 12 months, pending review)
        loan2_interest, loan2_total = loan_service.calculate_loan_totals(Decimal("5000.00"), Decimal("7.00"), 12)
        loan2 = Loan(
            loan_reference="LN-202611-392817",
            customer_id=cust2.id,
            principal_amount=Decimal("5000.00"),
            interest_rate=Decimal("7.00"),
            duration_months=12,
            total_payable=loan2_total,
            outstanding_balance=loan2_total,
            status=LoanStatus.APPLIED.value,
            applied_at=now - timedelta(days=3),
        )
        session.add(loan2)

        # 8. Initial Audit Logs
        session.add(
            AuditLog(
                user_id=admin_user.id,
                action="SYSTEM_INITIALIZED",
                target_entity="System",
                target_id="BMS-CORE",
                details='{"version": "1.0.0", "environment": "Demonstration"}',
                ip_address="127.0.0.1",
                timestamp=now - timedelta(days=60),
            )
        )
        session.add(
            AuditLog(
                user_id=admin_user.id,
                action="SEED_DATA_LOADED",
                target_entity="Database",
                target_id="ALL",
                details='{"status": "SUCCESS"}',
                ip_address="127.0.0.1",
                timestamp=now,
            )
        )

        logger.info("Demonstration data seeded successfully.")


if __name__ == "__main__":
    seed_demo_data()
    print("Demo data seeded successfully.")

