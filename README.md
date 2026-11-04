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

## Development and test data

The seed command creates deterministic demo users, accounts, categories, and
monthly records. Run database migrations first:

```bash
poetry run alembic upgrade head
```

Prepare the isolated demo database and apply all migrations:

```bash
poetry run python -m app.scripts.prepare_demo_database
```

Generate data in the demo database configured by `DEMO_DATABASE_URL` (or,
when omitted, a database named by adding `_demo` to the development database):

```bash
poetry run python -m app.scripts.seed_data
```

Generate the same data in the test database configured by
`TEST_DATABASE_URL`:

```bash
poetry run python -m app.scripts.seed_data --database test
```

Seeding the ordinary development database is possible only when explicitly
requested:

```bash
poetry run python -m app.scripts.seed_data --database development
```

Run the application against the isolated demo database:

```bash
poetry run python -m app.scripts.demo_server --reload --port 8010
```

The command securely prompts for one password shared by the demo users. Input
is hidden and must be confirmed. The password is never printed or logged.

For non-interactive CI/test execution, provide `SEED_DEMO_PASSWORD` through the
CI secret store or another secure environment injection mechanism. Do not put
the value in source control, README files, command arguments, or committed
`.env` files.

The command is repeatable: every run removes and recreates only these users and
their related data:

- `normal.demo@example.com` — common accounts, categories, several months, and
  grouped category records;
- `empty.demo@example.com` — accounts and categories without monthly records;
- `edge.demo@example.com` — inactive entities, minimum/maximum amounts, a null
  comment, and records across a year boundary.

Development seeding refuses to run when `APP_ENV` is not one of `dev`,
`development`, `local`, `test`, or `testing`. The test target always uses the
separate `TEST_DATABASE_URL`. The command never deletes non-demo users.

## Test coverage

Coverage reporting is configured through `pyproject.toml`. A normal full test
run automatically collects statement and branch coverage, prints missing lines,
creates an HTML report in `htmlcov/`, and writes Cobertura XML to
`coverage.xml`:

```bash
poetry run pytest
```

Open `htmlcov/index.html` in a browser for the navigable line-by-line report.
The suite fails when total coverage drops below 80%.

For a quick focused test run without calculating whole-application coverage:

```bash
poetry run pytest --no-cov tests/test_auth_api.py
```

Known gaps and the reasoning behind the threshold are documented in
`docs/test-coverage.md`.
