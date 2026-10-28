"""Database engine and session management."""
from __future__ import annotations

from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlmodel import SQLModel, create_engine

from src.config import settings

connect_args: dict[str, bool] = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args = {"check_same_thread": False}


def _set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
    if "sqlite" in settings.DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


engine: Engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args=connect_args,
    pool_pre_ping=True,
)

if "sqlite" in settings.DATABASE_URL:
    event.listen(engine, "connect", _set_sqlite_pragma)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
