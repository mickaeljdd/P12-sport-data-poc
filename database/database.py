from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from config import DATABASE_DIR, DATABASE_URL


def create_database_engine() -> Engine:
    DATABASE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    return create_engine(
        DATABASE_URL,
        future=True,
    )