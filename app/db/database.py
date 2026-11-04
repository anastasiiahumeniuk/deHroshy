import logging

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(settings.database_url)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def check_database_connection() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        logger.info(
            "Database connection successful",
            extra={"event": "database_connection_success"},
        )
        return True

    except SQLAlchemyError as exc:
        logger.error(
            "Database connection failed",
            extra={
                "event": "database_connection_error",
                "reason": type(exc).__name__,
            },
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        return False
