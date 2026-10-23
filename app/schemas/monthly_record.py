from decimal import Decimal

from pydantic import BaseModel, Field


class MonthlyRecordCreate(BaseModel):
    account_id: int
    category_id: int
    year: int = Field(gt=0)
    month: int = Field(ge=1, le=12)
    amount: Decimal = Field(gt=0)
    comment: str | None = None


class MonthlyRecordUpdate(BaseModel):
    account_id: int | None = None
    category_id: int | None = None
    year: int | None = Field(default=None, gt=0)
    month: int | None = Field(default=None, ge=1, le=12)
    amount: Decimal | None = Field(default=None, gt=0)
    comment: str | None = None


class MonthlyRecordResponse(BaseModel):
    id: int
    account_id: int
    category_id: int
    year: int
    month: int
    amount: Decimal
    comment: str | None

    model_config = {
        "from_attributes": True,
    }