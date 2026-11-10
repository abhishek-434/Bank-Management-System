"""Automated tests for bank account opening, minimum balance, and closing eligibility."""
from decimal import Decimal
from services.account_service import account_service
from config.constants import AccountTypeEnum, AccountStatus


def test_open_account_success(test_customer):
    """Verify account opening with initial deposit meeting minimum balance."""
    ok, acct, msg = account_service.open_account(
        customer_id=test_customer,
        account_type_code=AccountTypeEnum.SAVINGS.value,
        initial_deposit=Decimal("250.00"),
    )

    assert ok is True
    assert acct is not None
    assert acct.current_balance == Decimal("250.00")
    assert acct.status == AccountStatus.ACTIVE.value
    assert len(acct.account_number) == 10


def test_insufficient_initial_deposit_rejection(test_customer):
    """Verify account opening rejects deposit below minimum balance ($100 for Savings)."""
    ok, acct, msg = account_service.open_account(
        customer_id=test_customer,
        account_type_code=AccountTypeEnum.SAVINGS.value,
        initial_deposit=Decimal("50.00"),  # Below $100.00
    )

    assert ok is False
    assert "below the required minimum balance" in msg


def test_account_freezing_and_closure_rules(test_customer):
    """Verify account freeze and closure eligibility."""
    ok, acct, _ = account_service.open_account(
        customer_id=test_customer,
        account_type_code=AccountTypeEnum.SAVINGS.value,
        initial_deposit=Decimal("150.00"),
    )

    # 1. Freeze
    ok, msg = account_service.set_status(acct.id, AccountStatus.FROZEN.value)
    assert ok is True

    # 2. Closure attempt with positive balance should be rejected
    ok, msg = account_service.set_status(acct.id, AccountStatus.CLOSED.value)
    assert ok is False
    assert "Balance must be $0.00" in msg

