from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.category import CategoryType
from app.models.monthly_record import MonthlyRecord
from app.models.user import User
from app.schemas.monthly_record import (
    MonthlyRecordCreate,
    MonthlyRecordResponse,
    MonthlyRecordUpdate,
)
from app.services.monthly_records import (
    create_record,
    delete_record,
    list_records,
    update_record,
)
from app.services.periods import MAX_YEAR, MIN_YEAR


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
    return create_record(data, db, current_user.id)


@router.get(
    "",
    response_model=list[MonthlyRecordResponse],
)
def list_monthly_records(
    year: int = Query(ge=MIN_YEAR, le=MAX_YEAR),
    month: int = Query(ge=1, le=12),
    account_id: int | None = None,
    category_id: int | None = None,
    type: CategoryType | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MonthlyRecord]:
    return list_records(
        year,
        month,
        account_id,
        category_id,
        type,
        db,
        current_user.id,
    )


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
    return update_record(record_id, data, db, current_user.id)


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_monthly_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    delete_record(record_id, db, current_user.id)
