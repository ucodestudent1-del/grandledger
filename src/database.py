"""Database engine and session management."""
from __future__ import annotations

from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlmodel import SQLModel, create_engine

from src.config import settings

# Normalize postgresql:// to postgresql+psycopg:// for psycopg v3 driver
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

connect_args: dict[str, bool] = {}
if "sqlite" in database_url:
    connect_args = {"check_same_thread": False}


def _set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
    if "sqlite" in database_url:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


engine: Engine = create_engine(
    database_url,
    echo=settings.DEBUG,
    connect_args=connect_args,
    pool_pre_ping=True,
)

if "sqlite" in database_url:
    event.listen(engine, "connect", _set_sqlite_pragma)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
