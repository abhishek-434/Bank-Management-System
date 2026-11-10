"""Automated tests for deposits, withdrawals, overdraft protection, and limits."""
from decimal import Decimal
from services.transaction_service import transaction_service
from services.account_service import account_service
from config.constants import AccountStatus


def test_deposit_valid_amount(two_accounts):
    """Test successful deposit updates balance and ledger."""
    acct1, _ = two_accounts

    ok, receipt, msg = transaction_service.deposit(acct1, Decimal("500.00"), "Deposit Test")

    assert ok is True
    assert receipt["amount"] == Decimal("500.00")
    assert receipt["new_balance"] == Decimal("2500.00")  # 2000 initial + 500

    # Verify persistent balance
    acct = account_service.get_by_number(acct1)
    assert acct.current_balance == Decimal("2500.00")


def test_deposit_invalid_amount(two_accounts):
    """Test non-positive or malformed amounts are rejected."""
    acct1, _ = two_accounts

    # Zero amount
    ok, receipt, msg = transaction_service.deposit(acct1, Decimal("0.00"))
    assert ok is False
    assert "greater than zero" in msg

    # Negative amount
    ok, receipt, msg = transaction_service.deposit(acct1, Decimal("-50.00"))
    assert ok is False

    # More than 2 decimal places
    ok, receipt, msg = transaction_service.deposit(acct1, Decimal("10.555"))
    assert ok is False
    assert "2 decimal places" in msg


def test_withdrawal_success(two_accounts):
    """Test valid withdrawal updates balance."""
    acct1, _ = two_accounts  # Initial balance 2000.00, min 100.00

    ok, receipt, msg = transaction_service.withdraw(acct1, Decimal("300.00"), "Test Withdrawal")

    assert ok is True
    assert receipt["new_balance"] == Decimal("1700.00")


def test_withdrawal_insufficient_balance(two_accounts):
    """Test withdrawal exceeding available funds (protecting minimum balance) is rejected."""
    acct1, _ = two_accounts  # Balance 2000.00, min balance 100.00 -> available 1900.00

    # Attempt to withdraw 1950.00
    ok, receipt, msg = transaction_service.withdraw(acct1, Decimal("1950.00"))

    assert ok is False
    assert "Insufficient funds" in msg

    # Balance remains untouched
    acct = account_service.get_by_number(acct1)
    assert acct.current_balance == Decimal("2000.00")


def test_transaction_on_frozen_account(two_accounts):
    """Verify transactions are blocked on frozen accounts."""
    acct1, _ = two_accounts
    acct = account_service.get_by_number(acct1)
    account_service.set_status(acct.id, AccountStatus.FROZEN.value)

    # Deposit attempt
    ok, _, msg = transaction_service.deposit(acct1, Decimal("100.00"))
    assert ok is False
    assert "FROZEN" in msg

    # Withdrawal attempt
    ok, _, msg = transaction_service.withdraw(acct1, Decimal("50.00"))
    assert ok is False
    assert "FROZEN" in msg

