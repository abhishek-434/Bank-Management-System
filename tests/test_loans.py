"""Automated tests for loan calculation, approval, disbursement, and repayments."""
from decimal import Decimal
from services.loan_service import loan_service
from services.account_service import account_service
from config.constants import LoanStatus


def test_loan_interest_calculation():
    """Verify simplified educational loan interest calculation."""
    # Principal: $10,000, 6% annual, 12 months
    # Interest = (10000 * 6 * 12) / (100 * 12) = $600.00
    # Total = $10,600.00
    interest, total = loan_service.calculate_loan_totals(Decimal("10000.00"), Decimal("6.00"), 12)

    assert interest == Decimal("600.00")
    assert total == Decimal("10600.00")


def test_loan_lifecycle(two_accounts, test_customer):
    """Test full loan flow: Apply -> Approve & Disburse -> Repayment -> Closure."""
    acct1, _ = two_accounts

    # 1. Apply
    ok, loan, msg = loan_service.apply_for_loan(
        customer_id=test_customer,
        principal_input=Decimal("5000.00"),
        annual_rate=Decimal("10.00"),
        duration_months=12,
    )
    assert ok is True
    assert loan.status == LoanStatus.APPLIED.value
    # Total interest = (5000 * 10 * 12) / 1200 = 500.00. Total payable = 5500.00
    assert loan.total_payable == Decimal("5500.00")

    # 2. Approve & Disburse
    prev_balance = account_service.get_by_number(acct1).current_balance
    ok, msg = loan_service.review_loan(
        loan_id=loan.id,
        approve=True,
        disburse_account_number=acct1,
    )
    assert ok is True

    # Check disbursement credited account
    new_balance = account_service.get_by_number(acct1).current_balance
    assert new_balance == prev_balance + Decimal("5000.00")

    # 3. Partial Repayment
    ok, msg = loan_service.repay_loan(loan.id, Decimal("500.00"))
    assert ok is True
    assert "Remaining balance: $5,000.00" in msg

    # 4. Final Repayment to Pay Off Loan
    ok, msg = loan_service.repay_loan(loan.id, Decimal("5000.00"))
    assert ok is True
    assert "CLOSED" in msg

