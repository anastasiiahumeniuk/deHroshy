from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import MonthlyDashboardResponse
from app.services.financial import get_monthly_dashboard as build_dashboard
from app.services.periods import MAX_YEAR, MIN_YEAR


router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)


@router.get(
    "/monthly",
    response_model=MonthlyDashboardResponse,
)
def get_monthly_dashboard(
    year: int = Query(ge=MIN_YEAR, le=MAX_YEAR),
    month: int = Query(ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MonthlyDashboardResponse:
    return build_dashboard(db, current_user.id, year, month)
