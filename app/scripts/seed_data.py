import argparse
import logging
import os
import sys
from dataclasses import dataclass
from decimal import Decimal
from getpass import getpass
from collections.abc import Callable

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.core.logging import configure_logging
from app.core.security import hash_password
from app.models.account import Account
from app.models.category import Category, CategoryType
from app.models.monthly_record import MonthlyRecord
from app.models.user import User
from app.schemas.validation import validate_password_strength


logger = logging.getLogger(__name__)

SAFE_DEVELOPMENT_ENVIRONMENTS = {"dev", "development", "local", "test", "testing"}
SEED_PASSWORD_ENV_VAR = "SEED_DEMO_PASSWORD"


@dataclass(frozen=True)
class AccountSeed:
    name: str
    type: str
    is_active: bool = True


@dataclass(frozen=True)
class CategorySeed:
    name: str
    type: CategoryType
    is_active: bool = True


@dataclass(frozen=True)
class MonthlyRecordSeed:
    account: str
    category: str
    year: int
    month: int
    amount: Decimal
    comment: str | None = None


@dataclass(frozen=True)
class UserSeed:
    email: str
    accounts: tuple[AccountSeed, ...]
    categories: tuple[CategorySeed, ...]
    records: tuple[MonthlyRecordSeed, ...]


@dataclass(frozen=True)
class SeedSummary:
    users: int
    accounts: int
    categories: int
    monthly_records: int


SEED_USERS = (
    UserSeed(
        email="normal.demo@example.com",
        accounts=(
            AccountSeed("Main card", "card"),
            AccountSeed("Cash", "cash"),
            AccountSeed("Old savings", "bank", is_active=False),
        ),
        categories=(
            CategorySeed("Salary", CategoryType.INCOME),
            CategorySeed("Freelance", CategoryType.INCOME),
            CategorySeed("Housing", CategoryType.EXPENSE),
            CategorySeed("Food", CategoryType.EXPENSE),
            CategorySeed("Transport", CategoryType.EXPENSE),
            CategorySeed("Entertainment", CategoryType.EXPENSE),
            CategorySeed("Archived expense", CategoryType.EXPENSE, is_active=False),
        ),
        records=(
            MonthlyRecordSeed("Main card", "Salary", 2026, 9, Decimal("40000.00"), "September salary"),
            MonthlyRecordSeed("Old savings", "Archived expense", 2026, 9, Decimal("1200.00")),
            MonthlyRecordSeed("Main card", "Salary", 2026, 10, Decimal("40000.00"), "October salary"),
            MonthlyRecordSeed("Main card", "Freelance", 2026, 10, Decimal("5000.00")),
            MonthlyRecordSeed("Main card", "Housing", 2026, 10, Decimal("15000.00"), "Rent"),
            MonthlyRecordSeed("Main card", "Food", 2026, 10, Decimal("6000.00"), "Groceries"),
            MonthlyRecordSeed("Cash", "Food", 2026, 10, Decimal("1500.00"), "Cafes"),
            MonthlyRecordSeed("Main card", "Transport", 2026, 10, Decimal("2500.00")),
            MonthlyRecordSeed("Main card", "Entertainment", 2026, 10, Decimal("1200.00")),
            MonthlyRecordSeed("Main card", "Salary", 2026, 11, Decimal("20000.00")),
            MonthlyRecordSeed("Main card", "Housing", 2026, 11, Decimal("15000.00")),
            MonthlyRecordSeed("Main card", "Food", 2026, 11, Decimal("8000.00")),
        ),
    ),
    UserSeed(
        email="empty.demo@example.com",
        accounts=(AccountSeed("Empty account", "card"),),
        categories=(
            CategorySeed("Income", CategoryType.INCOME),
            CategorySeed("Expense", CategoryType.EXPENSE),
        ),
        records=(),
    ),
    UserSeed(
        email="edge.demo@example.com",
        accounts=(
            AccountSeed("Main edge account", "card"),
            AccountSeed("Inactive edge account", "cash", is_active=False),
        ),
        categories=(
            CategorySeed("Irregular income", CategoryType.INCOME),
            CategorySeed("Large expense", CategoryType.EXPENSE),
            CategorySeed("Inactive expense", CategoryType.EXPENSE, is_active=False),
        ),
        records=(
            MonthlyRecordSeed("Main edge account", "Irregular income", 2025, 12, Decimal("0.01")),
            MonthlyRecordSeed("Main edge account", "Large expense", 2026, 1, Decimal("9999999999.99"), "Maximum supported amount"),
            MonthlyRecordSeed("Inactive edge account", "Inactive expense", 2026, 1, Decimal("1.00")),
        ),
    ),
)

SEED_EMAILS = tuple(user.email for user in SEED_USERS)


def remove_existing_seed_users(db: Session) -> None:
    existing_users = db.scalars(
        select(User).where(User.email.in_(SEED_EMAILS))
    ).all()

    for user in existing_users:
        db.delete(user)

    db.flush()


def create_seed_user(db: Session, seed: UserSeed, password: str) -> None:
    user = User(
        email=seed.email,
        password_hash=hash_password(password),
    )
    db.add(user)
    db.flush()

    accounts = {
        account_seed.name: Account(
            user_id=user.id,
            name=account_seed.name,
            type=account_seed.type,
            is_active=account_seed.is_active,
        )
        for account_seed in seed.accounts
    }
    categories = {
        category_seed.name: Category(
            user_id=user.id,
            name=category_seed.name,
            type=category_seed.type,
            is_active=category_seed.is_active,
        )
        for category_seed in seed.categories
    }

    db.add_all((*accounts.values(), *categories.values()))
    db.flush()

    records = (
        MonthlyRecord(
            user_id=user.id,
            account_id=accounts[record_seed.account].id,
            category_id=categories[record_seed.category].id,
            year=record_seed.year,
            month=record_seed.month,
            amount=record_seed.amount,
            comment=record_seed.comment,
        )
        for record_seed in seed.records
    )
    db.add_all(records)


def generate_seed_data(db: Session, password: str) -> SeedSummary:
    """Replace only known demo users and return deterministic entity counts."""
    validate_password_strength(password)

    try:
        remove_existing_seed_users(db)

        for user_seed in SEED_USERS:
            create_seed_user(db, user_seed, password)

        db.commit()
    except Exception:
        db.rollback()
        raise

    return SeedSummary(
        users=len(SEED_USERS),
        accounts=sum(len(user.accounts) for user in SEED_USERS),
        categories=sum(len(user.categories) for user in SEED_USERS),
        monthly_records=sum(len(user.records) for user in SEED_USERS),
    )


def database_url_for_target(target: str) -> str:
    if target == "test":
        return settings.test_database_url

    if settings.app_env.lower() not in SAFE_DEVELOPMENT_ENVIRONMENTS:
        raise RuntimeError(
            "Seed generation is allowed only in development or testing environments"
        )

    if target == "development":
        return settings.database_url

    return settings.resolved_demo_database_url


def resolve_seed_password(
    prompt: Callable[[str], str] = getpass,
) -> str:
    environment_password = os.getenv(SEED_PASSWORD_ENV_VAR)
    if environment_password:
        return validate_password_strength(environment_password)

    if not sys.stdin.isatty():
        raise RuntimeError(
            f"Set {SEED_PASSWORD_ENV_VAR} for non-interactive seed generation"
        )

    password = prompt("Demo user password: ")
    confirmation = prompt("Confirm demo user password: ")

    if password != confirmation:
        raise ValueError("Demo user passwords do not match")

    return validate_password_strength(password)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate deterministic deHroshy development/test data.",
    )
    parser.add_argument(
        "--database",
        choices=("demo", "development", "test"),
        default="demo",
        help="Database target (default: demo).",
    )
    args = parser.parse_args()

    configure_logging(settings.log_level)
    seed_password = resolve_seed_password()
    engine = create_engine(database_url_for_target(args.database))
    seed_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    try:
        with seed_session() as db:
            summary = generate_seed_data(db, seed_password)
    finally:
        engine.dispose()

    logger.info(
        "Seed data generated",
        extra={"event": "seed_data_generated"},
    )
    print(
        "Generated "
        f"{summary.users} users, "
        f"{summary.accounts} accounts, "
        f"{summary.categories} categories, and "
        f"{summary.monthly_records} monthly records."
    )


if __name__ == "__main__":
    main()
