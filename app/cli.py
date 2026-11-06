from enum import Enum
from typing import Annotated

import typer
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.core.logging import configure_logging
from app.scripts.seed_data import (
    database_url_for_target,
    generate_seed_data,
    resolve_seed_password,
)


class DatabaseTarget(str, Enum):
    DEMO = "demo"
    DEVELOPMENT = "development"
    TEST = "test"


app = typer.Typer(
    name="dehroshy",
    help="Administrative commands for the deHroshy application.",
    no_args_is_help=True,
)


@app.callback()
def main() -> None:
    """deHroshy project administration CLI."""


@app.command("show-config")
def show_config() -> None:
    """Show safe application configuration values."""
    typer.echo(f"Environment: {settings.app_env}")
    typer.echo(f"Log level: {settings.log_level}")


@app.command("seed-data")
def seed_data(
    database: Annotated[
        DatabaseTarget,
        typer.Option(
            "--database",
            "-d",
            help="Database that will receive the demo data.",
        ),
    ] = DatabaseTarget.DEMO,
) -> None:
    """Generate deterministic users and financial data."""
    configure_logging(settings.log_level)
    engine = None

    try:
        password = resolve_seed_password()
        database_url = database_url_for_target(database.value)
        engine = create_engine(database_url)

        seed_session = sessionmaker(
            bind=engine,
            autoflush=False,
            autocommit=False,
        )

        with seed_session() as db:
            summary = generate_seed_data(db, password)

    except (ValueError, RuntimeError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    except SQLAlchemyError as exc:
        typer.echo(
            "Error: Could not generate data. Check the database connection.",
            err=True,
        )
        raise typer.Exit(code=1) from exc

    finally:
        if engine is not None:
            engine.dispose()

    typer.echo(
        f"Generated {summary.users} users, "
        f"{summary.accounts} accounts, "
        f"{summary.categories} categories and "
        f"{summary.monthly_records} monthly records."
    )


if __name__ == "__main__":
    app()
