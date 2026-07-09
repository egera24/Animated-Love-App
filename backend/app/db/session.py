from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

settings = get_settings()
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_llm_usage_provider_column()


def _migrate_llm_usage_provider_column() -> None:
    """Widen llm_usage.provider for provider/model keys (existing SQLite DBs)."""
    if engine.dialect.name != "sqlite":
        return
    with engine.connect() as conn:
        rows = conn.exec_driver_sql("PRAGMA table_info(llm_usage)").fetchall()
        if not rows:
            return
        col = next((r for r in rows if r[1] == "provider"), None)
        if col is None:
            return
        # PRAGMA: (cid, name, type, notnull, dflt_value, pk)
        col_type = str(col[2]).upper()
        if "96" in col_type:
            return
        conn.exec_driver_sql("ALTER TABLE llm_usage RENAME TO llm_usage_old")
        conn.exec_driver_sql(
            """
            CREATE TABLE llm_usage (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                usage_date VARCHAR(10) NOT NULL,
                provider VARCHAR(96) NOT NULL,
                calls INTEGER NOT NULL,
                tokens INTEGER NOT NULL,
                CONSTRAINT uq_llm_usage_date_provider UNIQUE (usage_date, provider)
            )
            """
        )
        conn.exec_driver_sql(
            """
            INSERT INTO llm_usage (id, usage_date, provider, calls, tokens)
            SELECT id, usage_date, provider, calls, tokens FROM llm_usage_old
            """
        )
        conn.exec_driver_sql("DROP TABLE llm_usage_old")
        conn.commit()
