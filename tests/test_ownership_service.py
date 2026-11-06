from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.category import Category, CategoryType
from app.models.monthly_record import MonthlyRecord
from app.services.ownership import (
    require_owned_account,
    require_owned_category,
    require_owned_monthly_record,
)


def test_ownership_services_return_owned_entities() -> None:
    db = MagicMock(spec=Session)
    account = Account(user_id=1, name="Main", type="card")
    category = Category(user_id=1, name="Food", type=CategoryType.EXPENSE)
    record = MonthlyRecord(
        user_id=1,
        account_id=1,
        category_id=1,
        year=2026,
        month=10,
        amount="100.00",
    )

    db.scalar.side_effect = [account, category, record]

    assert require_owned_account(db, 1, 1) is account
    assert require_owned_category(db, 1, 1) is category
    assert require_owned_monthly_record(db, 1, 1) is record


@pytest.mark.parametrize(
    ("service", "detail"),
    [
        (require_owned_account, "Account not found"),
        (require_owned_category, "Category not found"),
        (require_owned_monthly_record, "Monthly record not found"),
    ],
)
def test_ownership_services_hide_missing_or_foreign_entities(
    service,
    detail: str,
) -> None:
    db = MagicMock(spec=Session)
    db.scalar.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        service(db, 99, 1)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == detail
