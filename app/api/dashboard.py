from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.category import Category, CategoryType
from app.models.monthly_record import MonthlyRecord
from app.models.user import User
from app.schemas.dashboard import (
    CategorySummary,
    MonthlyDashboardResponse,
)


router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)


@router.get(
    "/monthly",
    response_model=MonthlyDashboardResponse,
)
def get_monthly_dashboard(
    year: int = Query(gt=0),
    month: int = Query(ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MonthlyDashboardResponse:
    grouped_query = (
        select(
            Category.id,
            Category.name,
            Category.type,
            func.sum(MonthlyRecord.amount).label("amount"),
        )
        .join(
            MonthlyRecord,
            MonthlyRecord.category_id == Category.id,
        )
        .where(
            MonthlyRecord.user_id == current_user.id,
            MonthlyRecord.year == year,
            MonthlyRecord.month == month,
        )
        .group_by(
            Category.id,
            Category.name,
            Category.type,
        )
        .order_by(
            func.sum(MonthlyRecord.amount).desc()
        )
    )

    rows = db.execute(grouped_query).all()

    total_income = Decimal("0.00")
    total_expenses = Decimal("0.00")

    income_by_category: list[CategorySummary] = []
    expenses_by_category: list[CategorySummary] = []

    for row in rows:
        if row.type == CategoryType.INCOME:
            total_income += row.amount

        if row.type == CategoryType.EXPENSE:
            total_expenses += row.amount

    for row in rows:
        if row.type == CategoryType.INCOME:
            percentage = (
                row.amount / total_income * 100
                if total_income > 0
                else Decimal("0.00")
            )

            income_by_category.append(
                CategorySummary(
                    category_id=row.id,
                    name=row.name,
                    amount=row.amount,
                    percentage=percentage.quantize(Decimal("0.01")),
                )
            )

        if row.type == CategoryType.EXPENSE:
            percentage = (
                row.amount / total_expenses * 100
                if total_expenses > 0
                else Decimal("0.00")
            )

            expenses_by_category.append(
                CategorySummary(
                    category_id=row.id,
                    name=row.name,
                    amount=row.amount,
                    percentage=percentage.quantize(Decimal("0.01")),
                )
            )

    difference = total_income - total_expenses

    savings_rate = (
        difference / total_income * 100
        if total_income > 0
        else None
    )

    if savings_rate is not None:
        savings_rate = savings_rate.quantize(
            Decimal("0.01")
        )

    return MonthlyDashboardResponse(
        year=year,
        month=month,
        total_income=total_income,
        total_expenses=total_expenses,
        difference=difference,
        savings_rate=savings_rate,
        income_by_category=income_by_category,
        expenses_by_category=expenses_by_category,
    )