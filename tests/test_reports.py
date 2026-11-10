"""Automated tests for reports, CSV exports, and PDF generator."""
from decimal import Decimal
import tempfile
import os
from services.report_service import report_service
from services.pdf_service import pdf_service
from services.transaction_service import transaction_service


def test_kpi_summary_and_dataframe(two_accounts):
    """Verify aggregated statistics."""
    acct1, _ = two_accounts
    transaction_service.deposit(acct1, Decimal("200.00"))

    kpis = report_service.get_kpi_summary()
    assert kpis["total_deposits"] >= Decimal("200.00")
    assert kpis["active_accounts"] >= 2

    df_dist = report_service.get_account_type_distribution()
    assert not df_dist.empty


def test_pdf_receipt_generation(two_accounts):
    """Verify ReportLab PDF generation executes without errors."""
    acct1, _ = two_accounts
    ok, receipt, _ = transaction_service.deposit(acct1, Decimal("150.00"), "PDF Test")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        out = pdf_service.generate_receipt_pdf(receipt, tmp_path)
        assert os.path.exists(out)
        assert os.path.getsize(out) > 1000  # Non-empty valid PDF
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

