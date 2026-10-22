from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user, hash_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.core.security import create_access_token, hash_password, verify_password
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


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

@router.post(
    "/login",
    response_model=TokenResponse,
    )
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
    ) -> TokenResponse:
    user = db.scalar(
        select(User).where(User.email == data.email)
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        subject=str(user.id)
    )

    return TokenResponse(
        access_token=access_token,
    )

@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user),
    ) -> dict[str, int | str]:
    return {
        "id": current_user.id,
        "email": current_user.email,
    }