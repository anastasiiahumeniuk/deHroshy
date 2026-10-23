from decimal import Decimal

from pydantic import BaseModel


class CategorySummary(BaseModel):
    category_id: int
    name: str
    amount: Decimal
    percentage: Decimal


class MonthlyDashboardResponse(BaseModel):
    year: int
    month: int

    total_income: Decimal
    total_expenses: Decimal
    difference: Decimal

    savings_rate: Decimal | None = None

    income_by_category: list[CategorySummary]
    expenses_by_category: list[CategorySummary]