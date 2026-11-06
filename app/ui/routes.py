from __future__ import annotations

import calendar
import secrets
from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path
from typing import TypedDict
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.accounts import (
    create_account as api_create_account,
    deactivate_account as api_deactivate_account,
    get_account as api_get_account,
    list_accounts as api_list_accounts,
    update_account as api_update_account,
)
from app.api.auth import login as api_login, register as api_register
from app.api.categories import (
    create_category as api_create_category,
    deactivate_category as api_deactivate_category,
    list_categories as api_list_categories,
    update_category as api_update_category,
)
from app.api.dashboard import get_monthly_dashboard
from app.api.monthly_records import (
    create_monthly_record as api_create_monthly_record,
    delete_monthly_record as api_delete_monthly_record,
    list_monthly_records as api_list_monthly_records,
    update_monthly_record as api_update_monthly_record,
)
from app.config import settings
from app.core.security import get_user_from_token
from app.db.session import get_db
from app.models.account import Account
from app.models.category import Category, CategoryType
from app.models.monthly_record import MonthlyRecord
from app.models.user import User
from app.schemas.accounts import AccountCreate, AccountUpdate
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.schemas.dashboard import CategorySummary
from app.schemas.monthly_record import MonthlyRecordCreate, MonthlyRecordUpdate
from app.services.ownership import (
    require_owned_category,
    require_owned_monthly_record,
)
from app.services.periods import resolve_period


router = APIRouter(prefix="/ui", tags=["ui"], include_in_schema=False)
templates = Jinja2Templates(
    directory=str(Path(__file__).resolve().parents[1] / "templates")
)
COOKIE_NAME = "access_token"
CSRF_COOKIE_NAME = "csrf_token"
INCOME_COLORS = ("#15825f", "#4ca77f", "#8bcaae", "#c5e7d7")
EXPENSE_COLORS = ("#ef6258", "#f5a04a", "#f7c467", "#8f82d8", "#53a8d8")


class UIAuthenticationRequired(Exception):
    """Raised when a browser page needs a valid login cookie."""


class PeriodContext(TypedDict):
    year: int
    month: int
    month_name: str
    previous_period: str
    next_period: str


class RecordFormContext(TypedDict):
    accounts: list[Account]
    categories: list[Category]


def current_ui_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise UIAuthenticationRequired

    try:
        return get_user_from_token(token, db)
    except HTTPException as exc:
        raise UIAuthenticationRequired from exc


def optional_ui_user(request: Request, db: Session) -> User | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        return get_user_from_token(token, db)
    except HTTPException:
        return None


def render(
    request: Request,
    name: str,
    *,
    current_user: User | None = None,
    status_code: int = 200,
    **context: object,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name=name,
        context={
            "current_user": current_user,
            "csrf_token": request.cookies.get(CSRF_COOKIE_NAME, ""),
            "form_data": {},
            **context,
        },
        status_code=status_code,
    )


def form_error(exc: ValidationError | HTTPException | IntegrityError) -> str:
    if isinstance(exc, ValidationError):
        first_error = exc.errors()[0]
        field = ".".join(str(item) for item in first_error["loc"])
        return f"{field.replace('_', ' ').title()}: {first_error['msg']}"
    if isinstance(exc, HTTPException):
        return str(exc.detail)
    return "An item with these details already exists."


def validate_csrf(request: Request, submitted_token: str) -> None:
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME, "")
    if not cookie_token or not secrets.compare_digest(cookie_token, submitted_token):
        raise HTTPException(status_code=403, detail="Invalid form security token")


def selected_period(year: int | None, month: int | None) -> tuple[int, int]:
    try:
        return resolve_period(year, month)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail="Invalid year or month",
        ) from exc


def period_link(year: int, month: int, offset: int) -> str:
    index = year * 12 + month - 1 + offset
    target_year, zero_based_month = divmod(index, 12)
    return f"?year={target_year}&month={zero_based_month + 1}"


def chart_style(
    items: Sequence[CategorySummary],
    colors: tuple[str, ...],
) -> str:
    if not items:
        return "conic-gradient(#e8eeeb 0% 100%)"

    stops: list[str] = []
    start = Decimal("0")
    for index, item in enumerate(items):
        end = Decimal("100") if index == len(items) - 1 else start + item.percentage
        color = colors[index % len(colors)]
        stops.append(f"{color} {start}% {end}%")
        start = end
    return f"conic-gradient({', '.join(stops)})"


def page_period_context(year: int, month: int) -> PeriodContext:
    return {
        "year": year,
        "month": month,
        "month_name": calendar.month_name[month],
        "previous_period": period_link(year, month, -1),
        "next_period": period_link(year, month, 1),
    }


def redirect_with_period(path: str, year: int, month: int, **params: str) -> RedirectResponse:
    query: dict[str, str | int] = {"year": year, "month": month, **params}
    return RedirectResponse(f"{path}?{urlencode(query)}", status_code=303)


def set_auth_cookies(response: RedirectResponse, access_token: str) -> None:
    secure = settings.app_env.lower() in {"production", "prod"}
    response.set_cookie(
        COOKIE_NAME,
        access_token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=secure,
        samesite="lax",
    )
    set_csrf_cookie(response, secrets.token_urlsafe(32), secure=secure)


def set_csrf_cookie(
    response: Response,
    csrf_token: str,
    *,
    secure: bool | None = None,
) -> None:
    if secure is None:
        secure = settings.app_env.lower() in {"production", "prod"}
    response.set_cookie(
        CSRF_COOKIE_NAME,
        csrf_token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=secure,
        samesite="lax",
    )


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)) -> Response:
    if optional_ui_user(request, db):
        return RedirectResponse("/ui/dashboard", status_code=303)
    csrf_token = request.cookies.get(CSRF_COOKIE_NAME) or secrets.token_urlsafe(32)
    response = render(
        request,
        "login.html",
        registered=request.query_params.get("registered") == "1",
        csrf_token=csrf_token,
    )
    if CSRF_COOKIE_NAME not in request.cookies:
        set_csrf_cookie(response, csrf_token)
    return response


@router.post("/login")
def login_action(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
) -> Response:
    validate_csrf(request, csrf_token)
    try:
        token = api_login(LoginRequest(email=email, password=password), db)
    except (ValidationError, HTTPException) as exc:
        return render(
            request,
            "login.html",
            error=form_error(exc),
            email=email,
            status_code=400 if isinstance(exc, ValidationError) else exc.status_code,
        )

    response = RedirectResponse("/ui/dashboard", status_code=303)
    set_auth_cookies(response, token.access_token)
    return response


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_db)) -> Response:
    if optional_ui_user(request, db):
        return RedirectResponse("/ui/dashboard", status_code=303)
    csrf_token = request.cookies.get(CSRF_COOKIE_NAME) or secrets.token_urlsafe(32)
    response = render(request, "register.html", csrf_token=csrf_token)
    if CSRF_COOKIE_NAME not in request.cookies:
        set_csrf_cookie(response, csrf_token)
    return response


@router.post("/register")
def register_action(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
) -> Response:
    validate_csrf(request, csrf_token)
    try:
        api_register(RegisterRequest(email=email, password=password), db)
    except (ValidationError, HTTPException) as exc:
        return render(
            request,
            "register.html",
            error=form_error(exc),
            email=email,
            status_code=400 if isinstance(exc, ValidationError) else exc.status_code,
        )
    return RedirectResponse("/ui/login?registered=1", status_code=303)


@router.post("/logout")
def logout_action(request: Request, csrf_token: str = Form("")) -> RedirectResponse:
    if request.cookies.get(CSRF_COOKIE_NAME):
        validate_csrf(request, csrf_token)
    response = RedirectResponse("/ui/login", status_code=303)
    response.delete_cookie(COOKIE_NAME)
    response.delete_cookie(CSRF_COOKIE_NAME)
    return response


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(
    request: Request,
    year: int | None = None,
    month: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_ui_user),
) -> HTMLResponse:
    year, month = selected_period(year, month)
    dashboard = get_monthly_dashboard(year, month, db, current_user)
    records = api_list_monthly_records(year, month, None, None, None, db, current_user)
    records = sorted(records, key=lambda record: record.id, reverse=True)[:5]
    return render(
        request,
        "dashboard.html",
        current_user=current_user,
        active_page="dashboard",
        dashboard=dashboard,
        records=records,
        income_chart=chart_style(dashboard.income_by_category, INCOME_COLORS),
        expense_chart=chart_style(dashboard.expenses_by_category, EXPENSE_COLORS),
        income_colors=INCOME_COLORS,
        expense_colors=EXPENSE_COLORS,
        **page_period_context(year, month),
    )


@router.get("/monthly-records", response_class=HTMLResponse)
def monthly_records_page(
    request: Request,
    year: int | None = None,
    month: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_ui_user),
) -> HTMLResponse:
    year, month = selected_period(year, month)
    records = api_list_monthly_records(year, month, None, None, None, db, current_user)
    return render(
        request,
        "monthly_records.html",
        current_user=current_user,
        active_page="records",
        records=sorted(records, key=lambda record: record.id, reverse=True),
        message=request.query_params.get("message"),
        **page_period_context(year, month),
    )


def record_form_context(
    db: Session,
    current_user: User,
    record: MonthlyRecord | None = None,
) -> RecordFormContext:
    accounts = [account for account in api_list_accounts(db, current_user) if account.is_active]
    categories = [category for category in api_list_categories(None, db, current_user) if category.is_active]
    if record is not None:
        if not record.account.is_active and record.account not in accounts:
            accounts.append(record.account)
        if not record.category.is_active and record.category not in categories:
            categories.append(record.category)
    return {"accounts": accounts, "categories": categories}


@router.get("/monthly-records/new", response_class=HTMLResponse)
def new_record_page(
    request: Request,
    year: int | None = None,
    month: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_ui_user),
) -> HTMLResponse:
    year, month = selected_period(year, month)
    return render(
        request,
        "monthly_record_form.html",
        current_user=current_user,
        active_page="records",
        title="Add monthly record",
        submit_label="Save record",
        form_data={"year": year, "month": month},
        **record_form_context(db, current_user),
    )


@router.post("/monthly-records/new")
def create_record_action(
    request: Request,
    account_id: str = Form(...),
    category_id: str = Form(...),
    year: str = Form(...),
    month: str = Form(...),
    amount: str = Form(...),
    comment: str = Form(""),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(current_ui_user),
) -> Response:
    validate_csrf(request, csrf_token)
    form_data = dict(account_id=account_id, category_id=category_id, year=year, month=month, amount=amount, comment=comment)
    try:
        data = MonthlyRecordCreate.model_validate(form_data)
        api_create_monthly_record(data, db, current_user)
    except (ValidationError, HTTPException) as exc:
        return render(
            request,
            "monthly_record_form.html",
            current_user=current_user,
            active_page="records",
            title="Add monthly record",
            submit_label="Save record",
            form_data=form_data,
            error=form_error(exc),
            status_code=400 if isinstance(exc, ValidationError) else exc.status_code,
            **record_form_context(db, current_user),
        )
    return redirect_with_period("/ui/monthly-records", data.year, data.month, message="Record added")


@router.get("/monthly-records/{record_id}/edit", response_class=HTMLResponse)
def edit_record_page(
    record_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_ui_user),
) -> HTMLResponse:
    record = require_owned_monthly_record(db, record_id, current_user.id)
    return render(
        request,
        "monthly_record_form.html",
        current_user=current_user,
        active_page="records",
        title="Edit monthly record",
        submit_label="Save changes",
        record=record,
        form_data=record,
        **record_form_context(db, current_user, record),
    )


@router.post("/monthly-records/{record_id}/edit")
def edit_record_action(
    record_id: int,
    request: Request,
    account_id: str = Form(...),
    category_id: str = Form(...),
    year: str = Form(...),
    month: str = Form(...),
    amount: str = Form(...),
    comment: str = Form(""),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(current_ui_user),
) -> Response:
    validate_csrf(request, csrf_token)
    record = require_owned_monthly_record(db, record_id, current_user.id)
    form_data = dict(account_id=account_id, category_id=category_id, year=year, month=month, amount=amount, comment=comment)
    try:
        data = MonthlyRecordUpdate.model_validate(form_data)
        updated = api_update_monthly_record(record_id, data, db, current_user)
    except (ValidationError, HTTPException) as exc:
        return render(
            request,
            "monthly_record_form.html",
            current_user=current_user,
            active_page="records",
            title="Edit monthly record",
            submit_label="Save changes",
            record=record,
            form_data=form_data,
            error=form_error(exc),
            status_code=400 if isinstance(exc, ValidationError) else exc.status_code,
            **record_form_context(db, current_user, record),
        )
    return redirect_with_period("/ui/monthly-records", updated.year, updated.month, message="Record updated")


@router.post("/monthly-records/{record_id}/delete")
def delete_record_action(
    record_id: int,
    request: Request,
    year: int = Form(...),
    month: int = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(current_ui_user),
) -> RedirectResponse:
    validate_csrf(request, csrf_token)
    api_delete_monthly_record(record_id, db, current_user)
    return redirect_with_period("/ui/monthly-records", year, month, message="Record deleted")


@router.get("/accounts", response_class=HTMLResponse)
def accounts_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_ui_user),
) -> HTMLResponse:
    return render(
        request,
        "accounts.html",
        current_user=current_user,
        active_page="accounts",
        accounts=api_list_accounts(db, current_user),
        message=request.query_params.get("message"),
    )


@router.post("/accounts")
def create_account_action(
    request: Request,
    name: str = Form(...),
    type: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(current_ui_user),
) -> Response:
    validate_csrf(request, csrf_token)
    try:
        api_create_account(AccountCreate(name=name, type=type), db, current_user)
    except (ValidationError, HTTPException, IntegrityError) as exc:
        db.rollback()
        return render(
            request,
            "accounts.html",
            current_user=current_user,
            active_page="accounts",
            accounts=api_list_accounts(db, current_user),
            form_data={"name": name, "type": type},
            error=form_error(exc),
            status_code=400,
        )
    return RedirectResponse("/ui/accounts?message=Account+added", status_code=303)


@router.get("/accounts/{account_id}/edit", response_class=HTMLResponse)
def edit_account_page(
    account_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_ui_user),
) -> HTMLResponse:
    account = api_get_account(account_id, db, current_user)
    return render(
        request,
        "entity_form.html",
        current_user=current_user,
        active_page="accounts",
        title="Edit account",
        item=account,
        fields=(
            {"name": "name", "label": "Account name", "value": account.name},
            {"name": "type", "label": "Account type", "value": account.type},
        ),
        cancel_url="/ui/accounts",
    )


@router.post("/accounts/{account_id}/edit")
def edit_account_action(
    account_id: int,
    request: Request,
    name: str = Form(...),
    type: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(current_ui_user),
) -> Response:
    validate_csrf(request, csrf_token)
    account = api_get_account(account_id, db, current_user)
    try:
        api_update_account(account_id, AccountUpdate(name=name, type=type), db, current_user)
    except (ValidationError, HTTPException, IntegrityError) as exc:
        db.rollback()
        return render(
            request,
            "entity_form.html",
            current_user=current_user,
            active_page="accounts",
            title="Edit account",
            item=account,
            fields=(
                {"name": "name", "label": "Account name", "value": name},
                {"name": "type", "label": "Account type", "value": type},
            ),
            cancel_url="/ui/accounts",
            error=form_error(exc),
            status_code=400,
        )
    return RedirectResponse("/ui/accounts?message=Account+updated", status_code=303)


@router.post("/accounts/{account_id}/deactivate")
def deactivate_account_action(
    account_id: int,
    request: Request,
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(current_ui_user),
) -> RedirectResponse:
    validate_csrf(request, csrf_token)
    api_deactivate_account(account_id, db, current_user)
    return RedirectResponse("/ui/accounts?message=Account+deactivated", status_code=303)


@router.get("/categories", response_class=HTMLResponse)
def categories_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_ui_user),
) -> HTMLResponse:
    return render(
        request,
        "categories.html",
        current_user=current_user,
        active_page="categories",
        categories=api_list_categories(None, db, current_user),
        message=request.query_params.get("message"),
    )


@router.post("/categories")
def create_category_action(
    request: Request,
    name: str = Form(...),
    type: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(current_ui_user),
) -> Response:
    validate_csrf(request, csrf_token)
    try:
        data = CategoryCreate.model_validate({"name": name, "type": type})
        api_create_category(data, db, current_user)
    except (ValidationError, HTTPException) as exc:
        return render(
            request,
            "categories.html",
            current_user=current_user,
            active_page="categories",
            categories=api_list_categories(None, db, current_user),
            form_data={"name": name, "type": type},
            error=form_error(exc),
            status_code=400,
        )
    return RedirectResponse("/ui/categories?message=Category+added", status_code=303)


@router.get("/categories/{category_id}/edit", response_class=HTMLResponse)
def edit_category_page(
    category_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_ui_user),
) -> HTMLResponse:
    category = require_owned_category(db, category_id, current_user.id)
    return render(
        request,
        "category_form.html",
        current_user=current_user,
        active_page="categories",
        category=category,
    )


@router.post("/categories/{category_id}/edit")
def edit_category_action(
    category_id: int,
    request: Request,
    name: str = Form(...),
    type: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(current_ui_user),
) -> Response:
    validate_csrf(request, csrf_token)
    category = require_owned_category(db, category_id, current_user.id)
    try:
        data = CategoryUpdate.model_validate({"name": name, "type": type})
        api_update_category(category_id, data, db, current_user)
    except (ValidationError, HTTPException) as exc:
        return render(
            request,
            "category_form.html",
            current_user=current_user,
            active_page="categories",
            category=category,
            form_data={"name": name, "type": type},
            error=form_error(exc),
            status_code=400,
        )
    return RedirectResponse("/ui/categories?message=Category+updated", status_code=303)


@router.post("/categories/{category_id}/deactivate")
def deactivate_category_action(
    category_id: int,
    request: Request,
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(current_ui_user),
) -> RedirectResponse:
    validate_csrf(request, csrf_token)
    api_deactivate_category(category_id, db, current_user)
    return RedirectResponse("/ui/categories?message=Category+deactivated", status_code=303)
