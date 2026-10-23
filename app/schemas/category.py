from pydantic import BaseModel, Field

from app.models.category import CategoryType


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: CategoryType


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    type: CategoryType | None = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    type: CategoryType
    is_active: bool

    model_config = {
        "from_attributes": True,
    }