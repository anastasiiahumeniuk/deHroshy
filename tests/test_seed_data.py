from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.engine import make_url

from app.core.security import verify_password
from app.config import settings
from app.models.account import Account
from app.models.category import Category
from app.models.monthly_record import MonthlyRecord
from app.models.user import User
from app.scripts.seed_data import (
    SEED_EMAILS,
    SEED_PASSWORD_ENV_VAR,
    SEED_USERS,
    generate_seed_data,
    resolve_seed_password,
)


TEST_SEED_PASSWORD = "TestSeedPassword1_"


def count_seed_entities(db_session) -> tuple[int, int, int, int]:
    user_ids = select(User.id).where(User.email.in_(SEED_EMAILS))

    users = db_session.scalar(
        select(func.count()).select_from(User).where(User.email.in_(SEED_EMAILS))
    )
    accounts = db_session.scalar(
        select(func.count()).select_from(Account).where(Account.user_id.in_(user_ids))
    )
    categories = db_session.scalar(
        select(func.count()).select_from(Category).where(Category.user_id.in_(user_ids))
    )
    records = db_session.scalar(
        select(func.count()).select_from(MonthlyRecord).where(MonthlyRecord.user_id.in_(user_ids))
    )
    return users, accounts, categories, records


def test_seed_data_generates_all_entity_types(db_session) -> None:
    summary = generate_seed_data(db_session, TEST_SEED_PASSWORD)

    assert count_seed_entities(db_session) == (
        summary.users,
        summary.accounts,
        summary.categories,
        summary.monthly_records,
    )

    normal_user = db_session.scalar(
        select(User).where(User.email == "normal.demo@example.com")
    )
    assert normal_user is not None
    assert verify_password(TEST_SEED_PASSWORD, normal_user.password_hash)


def test_seed_data_contains_normal_and_edge_scenarios(db_session) -> None:
    generate_seed_data(db_session, TEST_SEED_PASSWORD)

    empty_user = db_session.scalar(
        select(User).where(User.email == "empty.demo@example.com")
    )
    assert empty_user is not None
    assert empty_user.monthly_records == []

    assert db_session.scalar(
        select(func.count()).select_from(Account).where(
            Account.user_id.in_(select(User.id).where(User.email.in_(SEED_EMAILS))),
            Account.is_active.is_(False),
        )
    ) > 0
    assert db_session.scalar(
        select(func.count()).select_from(Category).where(
            Category.user_id.in_(select(User.id).where(User.email.in_(SEED_EMAILS))),
            Category.is_active.is_(False),
        )
    ) > 0

    amounts = set(
        db_session.scalars(
            select(MonthlyRecord.amount).where(
                MonthlyRecord.user_id.in_(
                    select(User.id).where(User.email.in_(SEED_EMAILS))
                )
            )
        ).all()
    )
    assert Decimal("0.01") in amounts
    assert Decimal("9999999999.99") in amounts


def test_seed_generation_is_repeatable(db_session) -> None:
    first_summary = generate_seed_data(db_session, TEST_SEED_PASSWORD)
    first_counts = count_seed_entities(db_session)

    second_summary = generate_seed_data(db_session, TEST_SEED_PASSWORD)
    second_counts = count_seed_entities(db_session)

    assert first_summary == second_summary
    assert first_counts == second_counts
    assert second_counts == (
        len(SEED_USERS),
        sum(len(user.accounts) for user in SEED_USERS),
        sum(len(user.categories) for user in SEED_USERS),
        sum(len(user.records) for user in SEED_USERS),
    )


def test_seed_password_can_be_read_from_environment(monkeypatch) -> None:
    monkeypatch.setenv(SEED_PASSWORD_ENV_VAR, TEST_SEED_PASSWORD)

    password = resolve_seed_password(
        prompt=lambda _: (_ for _ in ()).throw(AssertionError("Prompt was called"))
    )

    assert password == TEST_SEED_PASSWORD


def test_prompted_seed_password_must_match(monkeypatch) -> None:
    monkeypatch.delenv(SEED_PASSWORD_ENV_VAR, raising=False)
    monkeypatch.setattr("app.scripts.seed_data.sys.stdin.isatty", lambda: True)
    responses = iter((TEST_SEED_PASSWORD, "DifferentPassword1_"))

    try:
        resolve_seed_password(prompt=lambda _: next(responses))
    except ValueError as exc:
        assert str(exc) == "Demo user passwords do not match"
    else:
        raise AssertionError("Mismatched passwords were accepted")


def test_demo_database_is_separate_from_development_and_test() -> None:
    development = make_url(settings.database_url)
    test = make_url(settings.test_database_url)
    demo = make_url(settings.resolved_demo_database_url)

    assert demo.database != development.database
    assert demo.database != test.database
    if settings.demo_database_url is None:
        assert demo.database.endswith("_demo")
