# deHroshy

Personal finance tracker for monthly income and expense analysis.

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Pydantic
- Pytest

## MVP

- User authentication
- Multiple financial accounts
- Income and expense categories
- Monthly financial records
- Monthly dashboard
- Expense analytics
- Monthly history

## Run locally

```bash
uvicorn app.main:app --reload
```

## Database migrations

Create migration:

```bash
poetry run alembic revision --autogenerate -m "Migration name"
```

## Logging

Application logs are written to stderr as one JSON object per line. Each log
contains `timestamp`, `level`, `logger`, `message`, and an `event` identifier.
Relevant events can also contain safe context such as `reason`, `method`,
`path`, or `user_id`.

The application logs:

- application startup and shutdown;
- successful and failed database connection checks;
- registration and authentication outcomes;
- invalid JWT authentication attempts;
- unexpected application exceptions.

Passwords, access tokens, cookie values, and submitted email addresses are not
included in authentication failure logs.

The default log level is `INFO`. Override it with the `LOG_LEVEL` environment
variable:

```bash
LOG_LEVEL=DEBUG poetry run uvicorn app.main:app
```

Supported standard levels include `DEBUG`, `INFO`, `WARNING`, `ERROR`, and
`CRITICAL`. Unknown values fall back to `INFO`.
