from fastapi import FastAPI

from app.config import settings
from app.db.database import check_database_connection
from app.api.auth import router as auth_router
from app.api.accounts import router as accounts_router
from app.api.categories import router as categories_router

app = FastAPI(
    title=settings.app_name,
    description="Personal monthly finance tracker",
    version="0.1.0",
)


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