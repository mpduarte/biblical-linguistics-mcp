"""Database connection management."""

from __future__ import annotations

import os
from pathlib import Path

import aiosqlite

from .schema import SCHEMA_SQL

DEFAULT_DB_PATH = Path(__file__).resolve().parents[3] / "data" / "biblical_linguistics.db"

_db_path: Path | None = None


def set_db_path(path: str | Path) -> None:
    global _db_path
    _db_path = Path(path)


def get_db_path() -> Path:
    if _db_path is not None:
        return _db_path
    env = os.environ.get("BIBLICAL_LINGUISTICS_DB")
    if env:
        return Path(env)
    return DEFAULT_DB_PATH


async def get_connection() -> aiosqlite.Connection:
    """Open a connection to the database."""
    db_path = get_db_path()
    conn = await aiosqlite.connect(str(db_path))
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.execute("PRAGMA foreign_keys=ON")
    return conn


async def initialize_db(db_path: str | Path | None = None) -> None:
    """Create the database schema if it doesn't exist."""
    if db_path:
        set_db_path(db_path)
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(str(path))
    try:
        await conn.executescript(SCHEMA_SQL)
        await conn.commit()
    finally:
        await conn.close()
