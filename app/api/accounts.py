from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.schemas.accounts import AccountCreate, AccountResponse, AccountUpdate

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.account import Account
from app.models.user import User
from app.schemas.accounts import AccountCreate, AccountResponse
from sqlalchemy import select


router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
)


@router.post(
    "",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_account(
    data: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Account:
    account = Account(
        user_id=current_user.id,
        name=data.name,
        type=data.type,
    )

    db.add(account)
    db.commit()
    db.refresh(account)

    return account

@router.get(
    "",
    response_model=list[AccountResponse],
    )
def list_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ) -> list[Account]:
    accounts = db.scalars(
        select(Account).where(
            Account.user_id == current_user.id
        )
    ).all()

    return list(accounts)


@router.get(
    "/{account_id}",
    response_model=AccountResponse,
    )
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ) -> Account:
    account = db.scalar(
        select(Account).where(
            Account.id == account_id,
            Account.user_id == current_user.id,
        )
    )

    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    return account


@router.patch(
    "/{account_id}",
    response_model=AccountResponse,
)
def update_account(
    account_id: int,
    data: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ) -> Account:
    account = db.scalar(
        select(Account).where(
            Account.id == account_id,
            Account.user_id == current_user.id,
        )
    )

    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    if data.name is not None:
        account.name = data.name

    if data.type is not None:
        account.type = data.type

    db.commit()
    db.refresh(account)

    return account
@router.patch(
    "/{account_id}/deactivate",
    response_model=AccountResponse,
)


def deactivate_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ) -> Account:
    account = db.scalar(
        select(Account).where(
            Account.id == account_id,
            Account.user_id == current_user.id,
        )
    )

    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    account.is_active = False

    db.commit()
    db.refresh(account)

    return account