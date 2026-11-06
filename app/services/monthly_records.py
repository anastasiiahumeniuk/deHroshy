from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category, CategoryType
from app.models.monthly_record import MonthlyRecord
from app.schemas.monthly_record import MonthlyRecordCreate, MonthlyRecordUpdate
from app.services.ownership import (
    require_owned_account,
    require_owned_category,
    require_owned_monthly_record,
)
from app.services.periods import validate_period


def create_record(
    data: MonthlyRecordCreate,
    db: Session,
    user_id: int,
) -> MonthlyRecord:
    """Create a monthly record after validating its period and ownership."""
    validate_period(data.year, data.month)
    require_owned_account(db, data.account_id, user_id)
    require_owned_category(db, data.category_id, user_id)

    record = MonthlyRecord(
        user_id=user_id,
        account_id=data.account_id,
        category_id=data.category_id,
        year=data.year,
        month=data.month,
        amount=data.amount,
        comment=data.comment,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_records(
    year: int,
    month: int,
    account_id: int | None,
    category_id: int | None,
    category_type: CategoryType | None,
    db: Session,
    user_id: int,
) -> list[MonthlyRecord]:
    """List one user's records for a validated period and optional filters."""
    validate_period(year, month)
    query = (
        select(MonthlyRecord)
        .join(Category)
        .where(
            MonthlyRecord.user_id == user_id,
            MonthlyRecord.year == year,
            MonthlyRecord.month == month,
        )
    )

    if account_id is not None:
        query = query.where(MonthlyRecord.account_id == account_id)
    if category_id is not None:
        query = query.where(MonthlyRecord.category_id == category_id)
    if category_type is not None:
        query = query.where(Category.type == category_type)

    return list(db.scalars(query).all())


def update_record(
    record_id: int,
    data: MonthlyRecordUpdate,
    db: Session,
    user_id: int,
) -> MonthlyRecord:
    """Update a monthly record after validating ownership and its new period."""
    record = require_owned_monthly_record(db, record_id, user_id)
    new_year = data.year if data.year is not None else record.year
    new_month = data.month if data.month is not None else record.month
    validate_period(new_year, new_month)

    if data.account_id is not None:
        require_owned_account(db, data.account_id, user_id)
        record.account_id = data.account_id
    if data.category_id is not None:
        require_owned_category(db, data.category_id, user_id)
        record.category_id = data.category_id
    if data.year is not None:
        record.year = data.year
    if data.month is not None:
        record.month = data.month
    if data.amount is not None:
        record.amount = data.amount
    if "comment" in data.model_fields_set:
        record.comment = data.comment

    db.commit()
    db.refresh(record)
    return record


def delete_record(record_id: int, db: Session, user_id: int) -> None:
    """Delete a monthly record owned by the user."""
    record = require_owned_monthly_record(db, record_id, user_id)
    db.delete(record)
    db.commit()
