from pydantic import BaseModel, Field, field_validator

from app.models.category import CategoryType
from app.schemas.validation import normalize_name


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: CategoryType

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: object) -> object:
        return normalize_name(value, "Category name")


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    type: CategoryType | None = None

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: object) -> object:
        if value is None:
            return None
        return normalize_name(value, "Category name")


class CategoryResponse(BaseModel):
    id: int
    name: str
    type: CategoryType
    is_active: bool

    model_config = {
        "from_attributes": True,
    }
