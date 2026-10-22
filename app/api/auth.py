from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    )

def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
    ) -> dict[str, int | str]:
    existing_user = db.scalar(
        select(User).where(User.email == data.email)
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
    }