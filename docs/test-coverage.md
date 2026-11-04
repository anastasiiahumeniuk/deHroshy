# Test coverage

## Scope and threshold

`pytest-cov` measures statement and branch coverage for the complete `app`
package. The enforced project threshold is 80%. HTML and Cobertura XML reports
are generated during every full `pytest` run.

The current full-suite baseline is 83% branch-aware coverage (118 tests). Core
API business modules are at 99–100%, including authentication, dashboard,
accounts, categories, monthly records, database checks, and security.

The threshold includes server-rendered UI routes and operational CLI wrappers,
not only API business logic. The core dashboard, model, authentication,
accounts, categories, and monthly-record APIs have dedicated positive,
negative, ownership, validation, and edge-case tests.

## Important gaps addressed

The coverage review added tests for:

- duplicate registration and the authenticated `/auth/me` path;
- JWTs whose user no longer exists;
- duplicate account/category names during updates;
- cross-user account/category update and deactivation attempts;
- cross-user account/category assignment to monthly records;
- both successful and failed database connection logging;
- deterministic and repeatable seed generation, including edge data.

## Known coverage gaps

- `app/scripts/demo_server.py` is an operational wrapper around Uvicorn. Its
  process spawning and reload behavior is verified manually rather than from
  the unit-test process.
- `app/scripts/prepare_demo_database.py` creates a real PostgreSQL database and
  runs Alembic. Unit tests cover database URL separation; the actual
  create-database command remains an integration/manual check to avoid changing
  developer or CI PostgreSQL clusters during ordinary tests.
- Some rare server-rendered UI validation/error rendering branches are not
  individually asserted. Their underlying schemas and API business rules are
  covered directly, while core UI authentication, CRUD, isolation, empty-state,
  and CSRF flows have route tests.
- The `get_db` generator contains only session lifecycle plumbing. It is used by
  every API test through FastAPI dependency overrides, while its exact global
  `SessionLocal` construction is not tested separately.

These gaps are intentionally documented instead of using tests that launch
background servers, create external databases, or duplicate lower-level schema
and API assertions.
