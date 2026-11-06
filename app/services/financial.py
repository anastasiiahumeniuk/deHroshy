from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from decimal import ROUND_FLOOR, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category, CategoryType
from app.models.monthly_record import MonthlyRecord
from app.schemas.dashboard import CategorySummary, MonthlyDashboardResponse
from app.services.periods import validate_period


ZERO_AMOUNT = Decimal("0.00")
PERCENTAGE_FACTOR = Decimal("100")
PERCENTAGE_PRECISION = Decimal("0.01")
PERCENTAGE_UNITS = 10_000


@dataclass(frozen=True, slots=True)
class FinancialEntry:
    category_id: int
    category_name: str
    category_type: CategoryType
    amount: Decimal


def group_records_by_category(
    entries: Iterable[FinancialEntry],
) -> list[FinancialEntry]:
    """Combine financial entries by category and sort them by amount."""
    grouped: dict[int, FinancialEntry] = {}

    for entry in entries:
        existing = grouped.get(entry.category_id)
        if existing is None:
            grouped[entry.category_id] = entry
            continue

        grouped[entry.category_id] = FinancialEntry(
            category_id=entry.category_id,
            category_name=entry.category_name,
            category_type=entry.category_type,
            amount=existing.amount + entry.amount,
        )

    return sorted(
        grouped.values(),
        key=lambda entry: entry.amount,
        reverse=True,
    )


def calculate_monthly_totals(
    entries: Iterable[FinancialEntry],
) -> tuple[Decimal, Decimal]:
    """Return total income and total expenses."""
    total_income = ZERO_AMOUNT
    total_expenses = ZERO_AMOUNT

    for entry in entries:
        if entry.category_type == CategoryType.INCOME:
            total_income += entry.amount
        elif entry.category_type == CategoryType.EXPENSE:
            total_expenses += entry.amount

    return total_income, total_expenses


def calculate_savings_rate(
    total_income: Decimal,
    total_expenses: Decimal,
) -> Decimal | None:
    """Return saved income percentage, or None when there is no income."""
    if total_income <= ZERO_AMOUNT:
        return None

    difference = total_income - total_expenses
    return (
        difference / total_income * PERCENTAGE_FACTOR
    ).quantize(PERCENTAGE_PRECISION)


def build_category_summaries(
    entries: Sequence[FinancialEntry],
    category_type: CategoryType,
    total: Decimal,
) -> list[CategorySummary]:
    """Create category summaries with percentages for one category type."""
    matching_entries = [
        entry for entry in entries if entry.category_type == category_type
    ]
    if not matching_entries or total <= ZERO_AMOUNT:
        return []

    raw_units = [
        entry.amount / total * PERCENTAGE_UNITS
        for entry in matching_entries
    ]
    rounded_units = [
        int(value.to_integral_value(rounding=ROUND_FLOOR))
        for value in raw_units
    ]
    units_to_distribute = PERCENTAGE_UNITS - sum(rounded_units)
    remainder_order = sorted(
        range(len(raw_units)),
        key=lambda index: raw_units[index] - rounded_units[index],
        reverse=True,
    )
    for index in remainder_order[:units_to_distribute]:
        rounded_units[index] += 1

    return [
        CategorySummary(
            category_id=entry.category_id,
            name=entry.category_name,
            amount=entry.amount,
            percentage=(
                Decimal(units) / PERCENTAGE_FACTOR
            ).quantize(PERCENTAGE_PRECISION),
        )
        for entry, units in zip(matching_entries, rounded_units, strict=True)
    ]


def calculate_monthly_dashboard(
    year: int,
    month: int,
    entries: Iterable[FinancialEntry],
) -> MonthlyDashboardResponse:
    """Calculate all dashboard values from financial entries."""
    validate_period(year, month)
    grouped_entries = group_records_by_category(entries)
    total_income, total_expenses = calculate_monthly_totals(grouped_entries)

    return MonthlyDashboardResponse(
        year=year,
        month=month,
        total_income=total_income,
        total_expenses=total_expenses,
        difference=total_income - total_expenses,
        savings_rate=calculate_savings_rate(total_income, total_expenses),
        income_by_category=build_category_summaries(
            grouped_entries,
            CategoryType.INCOME,
            total_income,
        ),
        expenses_by_category=build_category_summaries(
            grouped_entries,
            CategoryType.EXPENSE,
            total_expenses,
        ),
    )


def get_monthly_dashboard(
    db: Session,
    user_id: int,
    year: int,
    month: int,
) -> MonthlyDashboardResponse:
    """Load one user's monthly entries and calculate their dashboard."""
    validate_period(year, month)
    query = (
        select(
            Category.id,
            Category.name,
            Category.type,
            MonthlyRecord.amount,
        )
        .join(MonthlyRecord, MonthlyRecord.category_id == Category.id)
        .where(
            MonthlyRecord.user_id == user_id,
            MonthlyRecord.year == year,
            MonthlyRecord.month == month,
        )
    )

    entries = (
        FinancialEntry(
            category_id=category_id,
            category_name=category_name,
            category_type=category_type,
            amount=amount,
        )
        for category_id, category_name, category_type, amount in db.execute(query)
    )
    return calculate_monthly_dashboard(year, month, entries)
