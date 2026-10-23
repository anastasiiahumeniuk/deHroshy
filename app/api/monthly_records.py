from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.account import Account
from app.models.category import Category
from app.models.monthly_record import MonthlyRecord
from app.models.user import User
from app.schemas.monthly_record import (
    MonthlyRecordCreate,
    MonthlyRecordResponse,
    MonthlyRecordUpdate,
)
from app.models.category import Category, CategoryType


router = APIRouter(
    prefix="/monthly-records",
    tags=["monthly-records"],
)


@router.post(
    "",
    response_model=MonthlyRecordResponse,
    status_code=status.HTTP_201_CREATED,
    )
def create_monthly_record(
    data: MonthlyRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ) -> MonthlyRecord:
    account = db.scalar(
        select(Account).where(
            Account.id == data.account_id,
            Account.user_id == current_user.id,
        )
    )

    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    category = db.scalar(
        select(Category).where(
            Category.id == data.category_id,
            Category.user_id == current_user.id,
        )
    )

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    record = MonthlyRecord(
        user_id=current_user.id,
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

@router.get(
    "",
    response_model=list[MonthlyRecordResponse],
    )
def list_monthly_records(
    year: int,
    month: int,
    account_id: int | None = None,
    category_id: int | None = None,
    type: CategoryType | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ) -> list[MonthlyRecord]:
    query = (
        select(MonthlyRecord)
        .join(Category)
        .where(
            MonthlyRecord.user_id == current_user.id,
            MonthlyRecord.year == year,
            MonthlyRecord.month == month,
        )
    )

    if account_id is not None:
        query = query.where(
            MonthlyRecord.account_id == account_id
        )

    if category_id is not None:
        query = query.where(
            MonthlyRecord.category_id == category_id
        )

    if type is not None:
        query = query.where(
            Category.type == type
        )

    records = db.scalars(query).all()

    return list(records)


@router.patch(
    "/{record_id}",
    response_model=MonthlyRecordResponse,
    )
def update_monthly_record(
    record_id: int,
    data: MonthlyRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ) -> MonthlyRecord:
    record = db.scalar(
        select(MonthlyRecord).where(
            MonthlyRecord.id == record_id,
            MonthlyRecord.user_id == current_user.id,
        )
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monthly record not found",
        )

    if data.account_id is not None:
        account = db.scalar(
            select(Account).where(
                Account.id == data.account_id,
                Account.user_id == current_user.id,
            )
        )

        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found",
            )

        record.account_id = data.account_id

    if data.category_id is not None:
        category = db.scalar(
            select(Category).where(
                Category.id == data.category_id,
                Category.user_id == current_user.id,
            )
        )

        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        record.category_id = data.category_id

    if data.year is not None:
        record.year = data.year

    if data.month is not None:
        record.month = data.month

    if data.amount is not None:
        record.amount = data.amount

    if data.comment is not None:
        record.comment = data.comment

    db.commit()
    db.refresh(record)

    return record


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    )
def delete_monthly_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ) -> None:
    record = db.scalar(
        select(MonthlyRecord).where(
            MonthlyRecord.id == record_id,
            MonthlyRecord.user_id == current_user.id,
        )
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monthly record not found",
        )

    db.delete(record)
    db.commit()