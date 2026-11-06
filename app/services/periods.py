from datetime import date


def validate_period(year: int, month: int) -> tuple[int, int]:
    """Validate and return a financial year and month."""
    if year < 1:
        raise ValueError("Year must be greater than zero")
    if month not in range(1, 13):
        raise ValueError("Month must be between 1 and 12")
    return year, month


def resolve_period(
    year: int | None,
    month: int | None,
    *,
    today: date | None = None,
) -> tuple[int, int]:
    """Fill missing period values from the current date and validate them."""
    current_date = today or date.today()
    return validate_period(
        year if year is not None else current_date.year,
        month if month is not None else current_date.month,
    )
