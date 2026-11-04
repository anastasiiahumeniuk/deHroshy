import argparse
import os

import uvicorn

from app.config import settings
from app.scripts.seed_data import SAFE_DEVELOPMENT_ENVIRONMENTS


def main() -> None:
    if settings.app_env.lower() not in SAFE_DEVELOPMENT_ENVIRONMENTS:
        raise RuntimeError(
            "Demo server is allowed only in development or testing environments"
        )

    parser = argparse.ArgumentParser(
        description="Run deHroshy using the isolated demo database.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8010)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    demo_database_url = settings.resolved_demo_database_url
    os.environ["DATABASE_URL"] = demo_database_url
    settings.database_url = demo_database_url

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
