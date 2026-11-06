from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    app_name: str
    app_env: str
    database_url: str
    test_database_url: str | None = None
    demo_database_url: str | None = None
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @property
    def resolved_demo_database_url(self) -> str:
        if self.demo_database_url:
            return self.demo_database_url

        development_url = make_url(self.database_url)
        if not development_url.database:
            raise ValueError("DATABASE_URL must include a database name")

        return development_url.set(
            database=f"{development_url.database}_demo"
        ).render_as_string(hide_password=False)


settings = Settings()
