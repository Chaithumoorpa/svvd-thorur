from decimal import Decimal
from typing import Annotated, Optional

from pydantic import AfterValidator, Field, PlainSerializer, StringConstraints


def _safe_url(value: str) -> str:
    """Only http(s) links or site-relative paths - blocks javascript:/data: URLs."""
    value = value.strip()
    if value == "":
        return value
    if value.startswith("/") and not value.startswith("//"):
        return value
    if value.lower().startswith(("http://", "https://")):
        return value
    raise ValueError("Must be an http(s) URL or a site-relative path")


SafeUrl = Annotated[str, StringConstraints(max_length=500), AfterValidator(_safe_url)]
OptionalSafeUrl = Optional[SafeUrl]


def blank_to_none(value):
    """Turn '' into None so empty form fields clear a value instead of storing ''."""
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


# Money: Decimal inside the app and database; JSON numbers on the wire (pydantic would
# otherwise emit strings, which breaks arithmetic in the browser).
MoneyOut = Annotated[Decimal, PlainSerializer(lambda v: float(v), return_type=float, when_used="json")]

# Positive money accepted from clients (max 9,999,999.99 fits Numeric(12,2)).
MoneyIn = Annotated[Decimal, Field(gt=0, le=Decimal("9999999.99"), max_digits=12, decimal_places=2)]
MoneyInOrZero = Annotated[Decimal, Field(ge=0, le=Decimal("9999999.99"), max_digits=12, decimal_places=2)]
