"""Cryptographically secure unique reference and identifier generators."""
import secrets
import string
from datetime import datetime, timezone


def generate_account_number(prefix: str = "100") -> str:
    """Generate a standard 10-digit bank account number starting with a prefix."""
    # Prefix (3 digits) + 7 secure random digits
    random_digits = "".join(secrets.choice(string.digits) for _ in range(7))
    return f"{prefix}{random_digits}"


def generate_transaction_ref(prefix: str = "TXN") -> str:
    """Generate a unique transaction reference formatted like TXN-YYYYMMDD-XXXXXX."""
    now_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_suffix = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"{prefix}-{now_str}-{random_suffix}"


def generate_transfer_ref(prefix: str = "TRF") -> str:
    """Generate a unique fund transfer reference."""
    now_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_suffix = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"{prefix}-{now_str}-{random_suffix}"


def generate_loan_ref(prefix: str = "LN") -> str:
    """Generate a unique loan reference number."""
    now_str = datetime.now(timezone.utc).strftime("%Y%m")
    random_suffix = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"{prefix}-{now_str}-{random_suffix}"


def generate_customer_code(prefix: str = "CUST") -> str:
    """Generate a unique customer identifier."""
    random_suffix = "".join(secrets.choice(string.digits) for _ in range(6))
    return f"{prefix}-{random_suffix}"


def generate_employee_code(prefix: str = "EMP") -> str:
    """Generate a unique employee identifier."""
    random_suffix = "".join(secrets.choice(string.digits) for _ in range(5))
    return f"{prefix}-{random_suffix}"

