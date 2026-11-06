from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.category import Category
from app.models.monthly_record import MonthlyRecord


def require_owned_account(
    db: Session,
    account_id: int,
    user_id: int,
) -> Account:
    """Return an account owned by the user or raise a safe 404 error."""
    account = db.scalar(
        select(Account).where(
            Account.id == account_id,
            Account.user_id == user_id,
        )
    )
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return account


def require_owned_category(
    db: Session,
    category_id: int,
    user_id: int,
) -> Category:
    """Return a category owned by the user or raise a safe 404 error."""
    category = db.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == user_id,
        )
    )
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    return category


def require_owned_monthly_record(
    db: Session,
    record_id: int,
    user_id: int,
) -> MonthlyRecord:
    """Return a monthly record owned by the user or raise a safe 404 error."""
    record = db.scalar(
        select(MonthlyRecord).where(
            MonthlyRecord.id == record_id,
            MonthlyRecord.user_id == user_id,
        )
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monthly record not found",
        )
    return record
