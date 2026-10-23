from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.category import Category
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryResponse
from app.models.category import Category, CategoryType
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate

router = APIRouter(
    prefix="/categories",
    tags=["categories"],
)


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ) -> Category:
    existing_category = db.scalar(
        select(Category).where(
            Category.user_id == current_user.id,
            Category.name == data.name,
            Category.type == data.type,
        )
    )

    if existing_category is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category with this name and type already exists",
        )

    category = Category(
        user_id=current_user.id,
        name=data.name,
        type=data.type,
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category

@router.get(
    "",
    response_model=list[CategoryResponse],
)
def list_categories(
    type: CategoryType | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ) -> list[Category]:
    query = select(Category).where(
        Category.user_id == current_user.id
    )

    if type is not None:
        query = query.where(
            Category.type == type
        )

    categories = db.scalars(query).all()

    return list(categories)


@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
    )
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ) -> Category:
    category = db.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == current_user.id,
        )
    )

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    new_name = data.name if data.name is not None else category.name
    new_type = data.type if data.type is not None else category.type

    duplicate = db.scalar(
        select(Category).where(
            Category.user_id == current_user.id,
            Category.name == new_name,
            Category.type == new_type,
            Category.id != category.id,
        )
    )

    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category with this name and type already exists",
        )

    if data.name is not None:
        category.name = data.name

    if data.type is not None:
        category.type = data.type

    db.commit()
    db.refresh(category)

    return category


@router.patch(
    "/{category_id}/deactivate",
    response_model=CategoryResponse,
    )
def deactivate_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ) -> Category:
    category = db.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == current_user.id,
        )
    )

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    category.is_active = False

    db.commit()
    db.refresh(category)

    return category