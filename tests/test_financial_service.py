from decimal import Decimal

from app.models.category import CategoryType
from app.services.financial import (
    FinancialEntry,
    calculate_monthly_dashboard,
    calculate_monthly_totals,
    group_records_by_category,
)


def entry(
    category_id: int,
    name: str,
    category_type: CategoryType,
    amount: str,
) -> FinancialEntry:
    return FinancialEntry(
        category_id=category_id,
        category_name=name,
        category_type=category_type,
        amount=Decimal(amount),
    )


def test_group_records_by_category_combines_and_sorts_entries() -> None:
    grouped = group_records_by_category(
        [
            entry(1, "Food", CategoryType.EXPENSE, "100.00"),
            entry(2, "Transport", CategoryType.EXPENSE, "250.00"),
            entry(1, "Food", CategoryType.EXPENSE, "200.00"),
        ]
    )

    assert [item.category_name for item in grouped] == ["Food", "Transport"]
    assert grouped[0].amount == Decimal("300.00")
    assert grouped[1].amount == Decimal("250.00")


def test_calculate_monthly_totals_separates_income_and_expenses() -> None:
    total_income, total_expenses = calculate_monthly_totals(
        [
            entry(1, "Salary", CategoryType.INCOME, "40000.00"),
            entry(2, "Freelance", CategoryType.INCOME, "5000.00"),
            entry(3, "Food", CategoryType.EXPENSE, "8000.00"),
        ]
    )

    assert total_income == Decimal("45000.00")
    assert total_expenses == Decimal("8000.00")


def test_calculate_monthly_dashboard_builds_percentages_and_savings() -> None:
    dashboard = calculate_monthly_dashboard(
        2026,
        10,
        [
            entry(1, "Salary", CategoryType.INCOME, "35000.00"),
            entry(2, "Freelance", CategoryType.INCOME, "5000.00"),
            entry(3, "Food", CategoryType.EXPENSE, "10000.00"),
        ],
    )

    assert dashboard.total_income == Decimal("40000.00")
    assert dashboard.total_expenses == Decimal("10000.00")
    assert dashboard.difference == Decimal("30000.00")
    assert dashboard.savings_rate == Decimal("75.00")
    assert dashboard.income_by_category[0].percentage == Decimal("87.50")
    assert dashboard.income_by_category[1].percentage == Decimal("12.50")
    assert dashboard.expenses_by_category[0].percentage == Decimal("100.00")


def test_calculate_monthly_dashboard_handles_empty_month() -> None:
    dashboard = calculate_monthly_dashboard(2026, 10, [])

    assert dashboard.total_income == Decimal("0.00")
    assert dashboard.total_expenses == Decimal("0.00")
    assert dashboard.difference == Decimal("0.00")
    assert dashboard.savings_rate is None
    assert dashboard.income_by_category == []
    assert dashboard.expenses_by_category == []
