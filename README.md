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

## Database migrations

Create migration:

```bash
poetry run alembic revision --autogenerate -m "Migration name"