from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base
from app.settings import get_settings


def create_app_engine(database_url: str | None = None) -> Engine:
    settings = get_settings()
    url = database_url or settings.database_url
    if url.startswith("sqlite:///"):
        db_path = url.replace("sqlite:///", "", 1)
        if db_path and db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args, future=True, pool_pre_ping=True)


engine = create_app_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    Base.metadata.create_all(engine)
    ensure_lightweight_schema_updates(engine)


def ensure_lightweight_schema_updates(target_engine: Engine) -> None:
    """Keep the simple SQLite deployment in step with additive model changes."""
    if not target_engine.url.get_backend_name().startswith("sqlite"):
        return
    inspector = inspect(target_engine)
    table_names = set(inspector.get_table_names())
    additions = {
        "api_channels": [
            ("adapter_type", "VARCHAR(32) DEFAULT 'custom_http'"),
        ],
        "model_configs": [
            ("metadata_json", "JSON"),
        ],
        "ai_generations": [
            ("options_json", "JSON"),
        ],
        "feishu_sync_runs": [
            ("error_summary", "TEXT DEFAULT ''"),
        ],
    }
    with target_engine.begin() as connection:
        for table, columns in additions.items():
            if table not in table_names:
                continue
            existing = {column["name"] for column in inspector.get_columns(table)}
            for name, ddl in columns:
                if name not in existing:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


def get_session() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
