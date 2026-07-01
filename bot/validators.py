"""
validators.py

Input validation for the trading bot CLI. Keeping validation isolated from
the CLI layer and the order-placement layer makes both easier to test and
means invalid input is rejected before any network call is made.
"""

import re
from decimal import Decimal, InvalidOperation
from typing import Optional


class ValidationError(Exception):
    """Raised when user-supplied input fails validation."""


# Basic symbol shape check: 5-15 uppercase letters/numbers, e.g. BTCUSDT.
# This intentionally does NOT hit the exchangeInfo endpoint so validation
# stays fast and offline; the exchange itself will reject unknown symbols.
_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{5,15}$")

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}


def validate_symbol(symbol: str) -> str:
    """
    Validate and normalize a trading symbol (e.g. 'btcusdt' -> 'BTCUSDT').
    """
    if not symbol or not isinstance(symbol, str):
        raise ValidationError("Symbol is required (e.g. BTCUSDT).")

    normalized = symbol.strip().upper()
    if not _SYMBOL_PATTERN.match(normalized):
        raise ValidationError(
            f"Invalid symbol '{symbol}'. Expected an uppercase alphanumeric "
            f"symbol like 'BTCUSDT' (5-15 characters)."
        )
    return normalized


def validate_side(side: str) -> str:
    """Validate order side is BUY or SELL."""
    if not side or not isinstance(side, str):
        raise ValidationError("Side is required (BUY or SELL).")

    normalized = side.strip().upper()
    if normalized not in VALID_SIDES:
        raise ValidationError(f"Invalid side '{side}'. Must be one of {sorted(VALID_SIDES)}.")
    return normalized


def validate_order_type(order_type: str) -> str:
    """Validate order type is MARKET or LIMIT."""
    if not order_type or not isinstance(order_type, str):
        raise ValidationError("Order type is required (MARKET or LIMIT).")

    normalized = order_type.strip().upper()
    if normalized not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. Must be one of {sorted(VALID_ORDER_TYPES)}."
        )
    return normalized


def validate_quantity(quantity) -> Decimal:
    """Validate quantity is a positive decimal number."""
    try:
        qty = Decimal(str(quantity))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError(f"Invalid quantity '{quantity}'. Must be a positive number.")

    if qty <= 0:
        raise ValidationError(f"Invalid quantity '{quantity}'. Must be greater than zero.")
    return qty


def validate_price(price, order_type: str) -> Optional[Decimal]:
    """
    Validate price. Required and must be positive for LIMIT orders.
    Ignored (returns None) for MARKET orders.
    """
    if order_type == "MARKET":
        return None

    # order_type == LIMIT from here on
    if price is None or str(price).strip() == "":
        raise ValidationError("Price is required for LIMIT orders.")

    try:
        px = Decimal(str(price))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError(f"Invalid price '{price}'. Must be a positive number.")

    if px <= 0:
        raise ValidationError(f"Invalid price '{price}'. Must be greater than zero.")
    return px


def validate_order_input(symbol: str, side: str, order_type: str, quantity, price=None) -> dict:
    """
    Run all validators and return a normalized dict of order parameters.
    Raises ValidationError on the first failure encountered.
    """
    normalized_type = validate_order_type(order_type)
    return {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": normalized_type,
        "quantity": validate_quantity(quantity),
        "price": validate_price(price, normalized_type),
    }
