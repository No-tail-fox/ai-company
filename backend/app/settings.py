from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = BACKEND_ROOT / "data" / "app.db"


class Settings(BaseSettings):
    app_name: str = "Light AI SaaS"
    api_prefix: str = "/api/v1"
    database_url: str = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"
    jwt_secret: str = "change-me-before-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60 * 24 * 7
    otp_default_code: str = "123456"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    storage_dir: str = str((BACKEND_ROOT / "storage").as_posix())

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

