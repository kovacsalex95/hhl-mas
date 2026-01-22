"""
Todo API - Database Layer

SQLite database with aiosqlite for async operations.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiosqlite

DB_PATH = Path(__file__).parent / "todos.db"

_connection: Optional[aiosqlite.Connection] = None


async def get_db() -> aiosqlite.Connection:
    """Get the database connection."""
    global _connection
    if _connection is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _connection


async def init_db() -> None:
    """Initialize the database connection and create tables."""
    global _connection
    _connection = await aiosqlite.connect(DB_PATH)
    _connection.row_factory = aiosqlite.Row

    await _connection.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    await _connection.commit()


async def close_db() -> None:
    """Close the database connection."""
    global _connection
    if _connection:
        await _connection.close()
        _connection = None


def utc_now() -> str:
    """Get current UTC timestamp as ISO string."""
    return datetime.now(timezone.utc).isoformat()
