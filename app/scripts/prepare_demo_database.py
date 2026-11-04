import argparse
import logging

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.config import settings
from app.core.logging import configure_logging
from app.scripts.seed_data import SAFE_DEVELOPMENT_ENVIRONMENTS


logger = logging.getLogger(__name__)


def create_demo_database_if_missing() -> bool:
    if settings.app_env.lower() not in SAFE_DEVELOPMENT_ENVIRONMENTS:
        raise RuntimeError(
            "Demo database preparation is allowed only in development or testing environments"
        )

    demo_url = make_url(settings.resolved_demo_database_url)
    if not demo_url.database:
        raise ValueError("DEMO_DATABASE_URL must include a database name")

    admin_url = demo_url.set(database="postgres")
    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

    try:
        with engine.connect() as connection:
            exists = connection.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": demo_url.database},
            )
            if exists:
                return False

            quoted_name = connection.dialect.identifier_preparer.quote(
                demo_url.database
            )
            connection.exec_driver_sql(f"CREATE DATABASE {quoted_name}")
            return True
    finally:
        engine.dispose()


def run_demo_migrations() -> None:
    original_database_url = settings.database_url
    settings.database_url = settings.resolved_demo_database_url

    try:
        command.upgrade(Config("alembic.ini"), "head")
    finally:
        settings.database_url = original_database_url


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create the isolated demo database and apply migrations.",
    )
    parser.parse_args()

    configure_logging(settings.log_level)
    created = create_demo_database_if_missing()
    run_demo_migrations()

    logger.info(
        "Demo database prepared",
        extra={"event": "demo_database_prepared"},
    )
    action = "created" if created else "already existed"
    print(f"Demo database {action}; migrations are up to date.")


if __name__ == "__main__":
    main()
