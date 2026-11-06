from unittest.mock import MagicMock

from typer.testing import CliRunner

from app import cli
from app.config import settings
from app.scripts.seed_data import SeedSummary


runner = CliRunner()


def test_show_config_command() -> None:
    result = runner.invoke(cli.app, ["show-config"])

    assert result.exit_code == 0
    assert f"Environment: {settings.app_env}" in result.output
    assert f"Log level: {settings.log_level}" in result.output


def test_seed_data_rejects_invalid_database() -> None:
    result = runner.invoke(
        cli.app,
        ["seed-data", "--database", "banana"],
    )

    assert result.exit_code == 2
    assert "Invalid value for '--database'" in result.output
    assert "banana" in result.output


def test_seed_data_command_generates_data(monkeypatch) -> None:
    fake_engine = MagicMock()
    fake_db = MagicMock()
    fake_session_factory = MagicMock()
    fake_session_factory.return_value.__enter__.return_value = fake_db

    database_url_mock = MagicMock(
        return_value="postgresql+psycopg://test:test@localhost/test"
    )
    create_engine_mock = MagicMock(return_value=fake_engine)
    generate_data_mock = MagicMock(
        return_value=SeedSummary(
            users=3,
            accounts=6,
            categories=12,
            monthly_records=15,
        )
    )

    monkeypatch.setattr(
        cli,
        "resolve_seed_password",
        lambda: "StrongTestPassword1_",
    )
    monkeypatch.setattr(cli, "database_url_for_target", database_url_mock)
    monkeypatch.setattr(cli, "create_engine", create_engine_mock)
    monkeypatch.setattr(
        cli,
        "sessionmaker",
        lambda **kwargs: fake_session_factory,
    )
    monkeypatch.setattr(cli, "generate_seed_data", generate_data_mock)

    result = runner.invoke(
        cli.app,
        ["seed-data", "--database", "test"],
    )

    assert result.exit_code == 0
    assert "Generated 3 users" in result.output
    assert "6 accounts" in result.output
    assert "12 categories" in result.output
    assert "15 monthly records" in result.output
    database_url_mock.assert_called_once_with("test")
    create_engine_mock.assert_called_once()
    generate_data_mock.assert_called_once_with(
        fake_db,
        "StrongTestPassword1_",
    )
    fake_engine.dispose.assert_called_once()


def test_seed_data_command_shows_understandable_error(monkeypatch) -> None:
    def raise_password_error() -> str:
        raise ValueError("Demo user passwords do not match")

    monkeypatch.setattr(cli, "resolve_seed_password", raise_password_error)

    result = runner.invoke(cli.app, ["seed-data"])

    assert result.exit_code == 1
    assert "Error: Demo user passwords do not match" in result.output
