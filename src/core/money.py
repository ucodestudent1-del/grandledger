"""Money safety: Decimal-only type validation for ledger amounts."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

MoneyValue = Decimal | int | str


def validate_decimal(value: Any, field_name: str = "amount") -> Decimal:
    """Convert a value to Decimal, rejecting floats and invalid types.

    Raises ValueError if the value is a float or cannot be converted to Decimal.
    """
    if isinstance(value, float):
        raise ValueError(f"{field_name} must be Decimal, not float: {value!r}")
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be Decimal, not bool: {value!r}")

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{field_name} is not a valid Decimal: {value!r}") from exc


def require_decimal(value: Any, field_name: str = "amount") -> None:
    """Assert that a value is already a Decimal (not float, int, or str).

    Use this at API boundaries to catch float drift before it reaches the DB.
    """
    if not isinstance(value, Decimal):
        raise TypeError(f"{field_name} must be Decimal, got {type(value).__name__}: {value!r}")


def is_balanced(debits: list[Decimal], credits: list[Decimal]) -> bool:
    """Check that total debits equal total credits."""
    return sum(debits, Decimal("0")) == sum(credits, Decimal("0"))


def quantize_money(value: Decimal, places: int = 4) -> Decimal:
    """Quantize a Decimal to the configured money precision (default 4 places)."""
    return value.quantize(Decimal("0.0001"))
