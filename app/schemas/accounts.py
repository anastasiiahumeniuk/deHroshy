from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.validation import normalize_account_type, normalize_name


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: str = Field(min_length=1, max_length=50)

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: object) -> object:
        return normalize_name(value, "Account name")

    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, value: object) -> object:
        return normalize_account_type(value)


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    type: str | None = Field(default=None, min_length=1, max_length=50)

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: object) -> object:
        if value is None:
            return None
        return normalize_name(value, "Account name")

    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, value: object) -> object:
        if value is None:
            return None
        return normalize_account_type(value)


class AccountResponse(BaseModel):
    id: int
    name: str
    type: str
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }
