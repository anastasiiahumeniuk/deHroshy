from decimal import Decimal
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.schemas.monthly_record import MonthlyRecordCreate
from app.services import monthly_records


def test_create_record_validates_ownership_and_persists(monkeypatch) -> None:
    db = MagicMock(spec=Session)
    account_check = MagicMock()
    category_check = MagicMock()
    monkeypatch.setattr(monthly_records, "require_active_account", account_check)
    monkeypatch.setattr(monthly_records, "require_active_category", category_check)
    data = MonthlyRecordCreate(
        account_id=10,
        category_id=20,
        year=2026,
        month=10,
        amount=Decimal("8500.50"),
        comment="October",
    )

    record = monthly_records.create_record(data, db, user_id=5)

    account_check.assert_called_once_with(db, 10, 5)
    category_check.assert_called_once_with(db, 20, 5)
    assert record.user_id == 5
    assert record.amount == Decimal("8500.50")
    db.add.assert_called_once_with(record)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(record)
