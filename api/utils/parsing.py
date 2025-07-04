from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

LOCALE_DECIMAL_SEP = ','
LOCALE_THOUSANDS_SEP = '.'


def parse_date(date_str: Optional[str]) -> Optional[str]:
    """Convert dd/mm/yyyy → YYYY-MM-DD for Odoo."""
    if not date_str:
        return None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return None


def parse_decimal(num) -> float:
    """Parse string with comma/point to float safely."""
    if num is None:
        return 0.0
    if isinstance(num, (int, float)):
        return float(num)
    if isinstance(num, str):
        clean = num.replace(LOCALE_THOUSANDS_SEP, '').replace(LOCALE_DECIMAL_SEP, '.')
        try:
            return float(Decimal(clean))
        except (InvalidOperation, ValueError):
            return 0.0
    return 0.0
