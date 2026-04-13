from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
from math import floor


def format_currency(value: float, digits: int = 2) -> str:
    quantizer = Decimal("1") if digits == 0 else Decimal("1." + ("0" * digits))
    rounded = Decimal(str(value)).quantize(quantizer, rounding=ROUND_HALF_UP)

    if digits == 0:
        return f"${int(rounded):,}"

    return f"${rounded:,.{digits}f}"


def format_rounded_annual(value: float) -> str:
    return f"{format_currency(value, 0)}/year"


def format_date(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    return parsed.strftime("%B %d, %Y").replace(" 0", " ")


def format_storage(gb: float) -> str:
    if gb <= 0:
        return "—"

    if gb >= 1000:
        terabytes = gb / 1000
        if int(gb) % 1000 == 0:
            return f"{terabytes:.0f} TB"
        return f"{terabytes:.1f} TB"

    return f"{gb:g} GB"


def format_user_range(range_description: str) -> str:
    return re.sub(r"\b(\d{4,})\b", _format_large_number, range_description)


def format_percent(value: float) -> str:
    return f"{floor(value + 0.5)}%"


def format_role_label(role: str) -> str:
    return " ".join(part.capitalize() for part in role.split("-") if part)


def _format_large_number(match: re.Match[str]) -> str:
    number = int(match.group(1))
    if number < 10000:
        return match.group(1)
    return f"{number:,}"
