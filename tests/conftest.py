"""Test configuration and in-memory test database setup."""
import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.base import Base
from database.connection import db_manager
from models.user import User
from models.customer import Customer
from models.account import Account, AccountType
from config.constants import AccountTypeEnum, UserRole, CustomerStatus, AccountStatus
from services.auth_service import auth_service


# Create in-memory SQLite engine with StaticPool
TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Bind db_manager to TEST_ENGINE immediately
db_manager._engine = TEST_ENGINE
db_manager._session_factory = sessionmaker(
    bind=TEST_ENGINE,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)
db_manager._active_dialect = "sqlite"

# Create schema and seed account types once for test session
Base.metadata.create_all(bind=TEST_ENGINE)
with db_manager.session_scope() as session:
    types = [
        AccountType(
            id=1,
            code=AccountTypeEnum.SAVINGS.value,
            name="Savings Account",
            minimum_balance=Decimal("100.00"),
            interest_rate=Decimal("3.50"),
            daily_withdrawal_limit=Decimal("50000.00"),
        ),
        AccountType(
            id=2,
            code=AccountTypeEnum.CURRENT.value,
            name="Current Account",
            minimum_balance=Decimal("500.00"),
            interest_rate=Decimal("0.00"),
            daily_withdrawal_limit=Decimal("100000.00"),
        ),
        AccountType(
            id=3,
            code=AccountTypeEnum.FIXED_DEPOSIT.value,
            name="Fixed Deposit",
            minimum_balance=Decimal("1000.00"),
            interest_rate=Decimal("6.50"),
            daily_withdrawal_limit=Decimal("0.00"),
        ),
    ]
    session.add_all(types)


@pytest.fixture(autouse=True)
def clean_database():
    """Ensure db_manager is bound and clean transient data after each test."""
    db_manager._engine = TEST_ENGINE
    db_manager._session_factory = sessionmaker(
        bind=TEST_ENGINE,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    db_manager._active_dialect = "sqlite"
    yield
    # Delete non-reference data
    with db_manager.session_scope() as session:
        for table in reversed(Base.metadata.sorted_tables):
            if table.name != "account_types":
                session.execute(table.delete())


@pytest.fixture
def test_user():
    """Create a standard active customer user."""
    with db_manager.session_scope() as session:
        user = User(
            username="test_customer",
            password_hash=auth_service.hash_password("Pass@1234"),
            role=UserRole.CUSTOMER.value,
            is_active=True,
        )
        session.add(user)
        session.flush()
        uid = user.id
    return uid


@pytest.fixture
def test_customer(test_user):
    """Create an active customer profile."""
    with db_manager.session_scope() as session:
        cust = Customer(
            user_id=test_user,
            customer_code="CUST-TEST01",
            first_name="Jane",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            email="jane.doe@test.com",
            phone="+1-555-0999",
            address="123 Test Street",
            govt_id_masked="ID-***-9999",
            status=CustomerStatus.ACTIVE.value,
        )
        session.add(cust)
        session.flush()
        cid = cust.id
    return cid


@pytest.fixture
def two_accounts(test_customer):
    """Create two test accounts for transfer and transaction tests."""
    with db_manager.session_scope() as session:
        acct1 = Account(
            account_number="1000000001",
            customer_id=test_customer,
            account_type_id=1,  # Savings (Min balance 100.00)
            current_balance=Decimal("2000.00"),
            currency="USD",
            status=AccountStatus.ACTIVE.value,
        )
        acct2 = Account(
            account_number="1000000002",
            customer_id=test_customer,
            account_type_id=1,
            current_balance=Decimal("500.00"),
            currency="USD",
            status=AccountStatus.ACTIVE.value,
        )
        session.add_all([acct1, acct2])
        session.flush()
        a1, a2 = acct1.account_number, acct2.account_number
    return a1, a2
