"""Data formatters for currency, timestamps, and data masking."""
from decimal import Decimal
from datetime import datetime
from typing import Union


def format_currency(amount: Union[Decimal, float, int, None], symbol: str = "$") -> str:
    """Format an amount as a clean currency string with 2 decimal places."""
    if amount is None:
        return f"{symbol}0.00"
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    return f"{symbol}{amount:,.2f}"


def format_datetime(dt: Union[datetime, None], fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format a datetime object into a user-friendly string."""
    if not dt:
        return "N/A"
    return dt.strftime(fmt)


def format_date(dt: Union[datetime, None], fmt: str = "%Y-%m-%d") -> str:
    """Format a date or datetime object into YYYY-MM-DD."""
    if not dt:
        return "N/A"
    return dt.strftime(fmt)


def mask_account_number(account_num: str) -> str:
    """Mask account number showing only last 4 digits (e.g. ****1234)."""
    if not account_num:
        return ""
    clean = str(account_num).strip()
    if len(clean) <= 4:
        return clean
    return "*" * (len(clean) - 4) + clean[-4:]


def mask_id_number(id_str: str) -> str:
    """Mask government ID reference showing last 3 characters."""
    if not id_str:
        return "N/A"
    clean = str(id_str).strip()
    if len(clean) <= 3:
        return clean
    return "*" * (len(clean) - 3) + clean[-3:]

