from datetime import datetime

from pydantic import BaseModel, Field


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: str = Field(min_length=1, max_length=50)


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    type: str | None = Field(default=None, min_length=1, max_length=50)


class AccountResponse(BaseModel):
    id: int
    name: str
    type: str
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }