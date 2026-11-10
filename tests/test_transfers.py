"""Automated tests for fund transfers, atomicity, and duplicate prevention."""
from decimal import Decimal
from services.transaction_service import transaction_service
from services.account_service import account_service


def test_atomic_transfer_success(two_accounts):
    """Verify atomic internal transfer debits sender and credits receiver."""
    acct1, acct2 = two_accounts  # acct1: 2000.00, acct2: 500.00

    ok, receipt, msg = transaction_service.transfer(
        sender_account_no=acct1,
        receiver_account_no=acct2,
        amount_input=Decimal("400.00"),
        description="Transfer test",
    )

    assert ok is True
    assert receipt["amount"] == Decimal("400.00")
    assert receipt["sender_new_balance"] == Decimal("1600.00")

    # Verify both accounts in DB
    sender = account_service.get_by_number(acct1)
    receiver = account_service.get_by_number(acct2)

    assert sender.current_balance == Decimal("1600.00")
    assert receiver.current_balance == Decimal("900.00")


def test_transfer_to_same_account_rejection(two_accounts):
    """Verify system rejects transfer where sender equals receiver."""
    acct1, _ = two_accounts

    ok, receipt, msg = transaction_service.transfer(acct1, acct1, Decimal("100.00"))

    assert ok is False
    assert "must be different" in msg


def test_transfer_insufficient_funds(two_accounts):
    """Verify transfer fails and rolls back cleanly when funds are insufficient."""
    acct1, acct2 = two_accounts  # acct1: 2000.00 (available 1900.00)

    ok, receipt, msg = transaction_service.transfer(
        sender_account_no=acct1,
        receiver_account_no=acct2,
        amount_input=Decimal("2500.00"),
    )

    assert ok is False
    assert "Insufficient funds" in msg

    # Balances must remain unchanged
    sender = account_service.get_by_number(acct1)
    receiver = account_service.get_by_number(acct2)
    assert sender.current_balance == Decimal("2000.00")
    assert receiver.current_balance == Decimal("500.00")


def test_transfer_to_nonexistent_account(two_accounts):
    """Verify transfer rejects invalid target account."""
    acct1, _ = two_accounts

    ok, receipt, msg = transaction_service.transfer(
        sender_account_no=acct1,
        receiver_account_no="9999999999",
        amount_input=Decimal("100.00"),
    )

    assert ok is False
    assert "does not exist" in msg

