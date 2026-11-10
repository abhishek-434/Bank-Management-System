"""Input validation and security rule verification utilities."""
import re
from decimal import Decimal, InvalidOperation
from typing import Tuple, Optional


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^\+?[0-9\s\-()]{7,20}$")


def validate_email(email: str) -> bool:
    """Validate email address format."""
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def validate_phone(phone: str) -> bool:
    """Validate phone number string."""
    if not phone or not isinstance(phone, str):
        return False
    return bool(PHONE_REGEX.match(phone.strip()))


def validate_positive_amount(amount_input: object) -> Tuple[bool, Optional[Decimal], str]:
    """
    Validate that an amount is positive, has at most 2 decimal places,
    and returns (is_valid, Decimal_amount, error_message).
    """
    if amount_input is None:
        return False, None, "Amount cannot be empty."

    val_str = str(amount_input).strip().replace(",", "")
    if not val_str:
        return False, None, "Amount cannot be empty."

    try:
        amt = Decimal(val_str)
    except (InvalidOperation, TypeError, ValueError):
        return False, None, "Invalid numerical amount."

    if amt.is_nan() or amt.is_infinite():
        return False, None, "Invalid numerical amount."

    if amt <= Decimal("0.00"):
        return False, None, "Amount must be strictly greater than zero."

    # Verify decimal precision (maximum 2 decimal places)
    quantized = amt.quantize(Decimal("0.01"))
    if abs(amt - quantized) > Decimal("0.000000001"):
        return False, None, "Amount cannot have more than 2 decimal places."

    return True, quantized, ""


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special symbol
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one digit."
    if not re.search(r"[@$!%*?&#^+=_-]", password):
        return False, "Password must contain at least one special character (@$!%*?&#^+=_-)."
    return True, ""

