from datetime import date

import pytest

from app.services.periods import resolve_period, validate_period


def test_validate_period_returns_valid_values() -> None:
    assert validate_period(2026, 10) == (2026, 10)


@pytest.mark.parametrize(
    ("year", "month", "message"),
    [
        (0, 10, "Year must be greater than zero"),
        (2026, 0, "Month must be between 1 and 12"),
        (2026, 13, "Month must be between 1 and 12"),
    ],
)
def test_validate_period_rejects_invalid_values(
    year: int,
    month: int,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        validate_period(year, month)


def test_resolve_period_uses_current_values_when_missing() -> None:
    assert resolve_period(None, None, today=date(2026, 11, 6)) == (2026, 11)
    assert resolve_period(2025, None, today=date(2026, 11, 6)) == (2025, 11)
