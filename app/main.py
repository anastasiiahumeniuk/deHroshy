import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db.database import check_database_connection
from app.api.auth import router as auth_router
from app.api.accounts import router as accounts_router
from app.api.categories import router as categories_router
from app.api.monthly_records import router as monthly_records_router
from app.api.dashboard import router as dashboard_router
from app.core.logging import configure_logging
from app.ui.routes import UIAuthenticationRequired, router as ui_router

configure_logging(settings.log_level)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Application startup",
        extra={"event": "application_startup"},
    )

    try:
        yield
    finally:
        logger.info(
            "Application shutdown",
            extra={"event": "application_shutdown"},
        )


app = FastAPI(
    title=settings.app_name,
    description="Personal monthly finance tracker",
    version="0.1.0",
    lifespan=lifespan,
)

app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent / "static"),
    name="static",
)


@app.exception_handler(Exception)
def unexpected_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.error(
        "Unexpected application error",
        extra={
            "event": "unexpected_application_error",
            "method": request.method,
            "path": request.url.path,
        },
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.exception_handler(UIAuthenticationRequired)
def ui_authentication_required(
    request: Request,
    exc: UIAuthenticationRequired,
) -> RedirectResponse:
    response = RedirectResponse(
        url=f"/ui/login?next={request.url.path}",
        status_code=303,
    )
    response.delete_cookie("access_token")
    return response


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/ui/dashboard", status_code=303)


@app.get("/health")
def health_check() -> dict[str, str]:
    database_status = (
        "connected"
        if check_database_connection()
        else "disconnected"
    )

    return {
        "status": "ok",
        "environment": settings.app_env,
        "database": database_status,
    }

app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(categories_router)
app.include_router(monthly_records_router)
app.include_router(dashboard_router)
app.include_router(ui_router)
