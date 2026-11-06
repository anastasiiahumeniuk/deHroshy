from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.schemas.validation import (
    normalize_amount,
    normalize_optional_comment,
)
from app.services.periods import MAX_YEAR, MIN_YEAR


class MonthlyRecordCreate(BaseModel):
    account_id: int = Field(gt=0)
    category_id: int = Field(gt=0)
    year: int = Field(ge=MIN_YEAR, le=MAX_YEAR)
    month: int = Field(ge=1, le=12)
    amount: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2,
    )
    comment: str | None = Field(default=None, max_length=500)

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, value: object) -> object:
        return normalize_amount(value)

    @field_validator("comment", mode="before")
    @classmethod
    def validate_comment(cls, value: object) -> object:
        return normalize_optional_comment(value)


class MonthlyRecordUpdate(BaseModel):
    account_id: int | None = Field(default=None, gt=0)
    category_id: int | None = Field(default=None, gt=0)
    year: int | None = Field(default=None, ge=MIN_YEAR, le=MAX_YEAR)
    month: int | None = Field(default=None, ge=1, le=12)
    amount: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=2,
    )
    comment: str | None = Field(default=None, max_length=500)

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, value: object) -> object:
        if value is None:
            return None

        return normalize_amount(value)

    @field_validator("comment", mode="before")
    @classmethod
    def validate_comment(cls, value: object) -> object:
        return normalize_optional_comment(value)


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
