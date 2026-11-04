import asyncio
import json
import logging
from unittest.mock import patch

from fastapi import Request
from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import JsonFormatter
from app.db import database
from app.main import app, lifespan, unexpected_error_handler


def test_json_formatter_adds_structured_context() -> None:
    record = logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Test event",
        args=(),
        exc_info=None,
    )
    record.event = "test_event"
    record.user_id = 42

    payload = json.loads(JsonFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "app.test"
    assert payload["message"] == "Test event"
    assert payload["event"] == "test_event"
    assert payload["user_id"] == 42
    assert "timestamp" in payload


def test_lifespan_logs_startup_and_shutdown() -> None:
    async def run_lifespan() -> None:
        async with lifespan(app):
            pass

    with patch("app.main.logger.info") as log_info:
        asyncio.run(run_lifespan())

    events = [call.kwargs["extra"]["event"] for call in log_info.call_args_list]
    assert events == ["application_startup", "application_shutdown"]


def test_database_connection_error_is_logged(monkeypatch) -> None:
    def fail_to_connect():
        raise SQLAlchemyError("database unavailable")

    monkeypatch.setattr(database.engine, "connect", fail_to_connect)

    with patch("app.db.database.logger.error") as log_error:
        assert database.check_database_connection() is False

    assert log_error.call_args.kwargs["extra"] == {
        "event": "database_connection_error",
        "reason": "SQLAlchemyError",
    }


def test_authentication_failure_log_does_not_expose_credentials(client) -> None:
    email = "private-login@example.com"
    password = "SecretPassword1_"

    with patch("app.api.auth.logger.warning") as log_warning:
        response = client.post(
            "/auth/login",
            json={"email": email, "password": password},
        )

    assert response.status_code == 401
    logged_call = repr(log_warning.call_args)
    assert email not in logged_call
    assert password not in logged_call
    assert log_warning.call_args.kwargs["extra"] == {
        "event": "authentication_failure",
        "reason": "unknown_user",
    }


def test_invalid_token_log_does_not_expose_token(client) -> None:
    token = "sensitive-invalid-token"

    with patch("app.core.security.logger.warning") as log_warning:
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 401
    assert token not in repr(log_warning.call_args)
    assert log_warning.call_args.kwargs["extra"] == {
        "event": "authentication_failure",
        "reason": "invalid_token",
    }


def test_unexpected_error_is_logged_and_hidden_from_client() -> None:
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/broken",
            "headers": [],
            "query_string": b"",
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("testclient", 50000),
        }
    )
    error = RuntimeError("internal details")

    with patch("app.main.logger.error") as log_error:
        response = unexpected_error_handler(request, error)

    assert response.status_code == 500
    assert response.body == b'{"detail":"Internal server error"}'
    assert log_error.call_args.kwargs["extra"] == {
        "event": "unexpected_application_error",
        "method": "GET",
        "path": "/broken",
    }
