"""SQLite database layer for Todo API."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DATABASE_PATH = Path(__file__).parent / "todos.db"

# Use synchronous sqlite3 for simplicity and reliability
_connection: Optional[sqlite3.Connection] = None


def get_connection() -> sqlite3.Connection:
    """Get or create the database connection."""
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        _connection.row_factory = sqlite3.Row
    return _connection


def close_connection() -> None:
    """Close the database connection."""
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None


async def init_db() -> None:
    """Initialize the database schema."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()


async def create_todo(title: str, description: Optional[str], completed: bool) -> dict:
    """Create a new todo item."""
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT INTO todos (title, description, completed, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (title, description, completed, now, now),
    )
    conn.commit()
    todo_id = cursor.lastrowid

    cursor = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
    row = cursor.fetchone()
    return dict(row)


async def get_todo(todo_id: int) -> Optional[dict]:
    """Get a todo by ID."""
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


async def get_all_todos() -> list[dict]:
    """Get all todos."""
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM todos ORDER BY created_at DESC")
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


async def update_todo(
    todo_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    completed: Optional[bool] = None,
) -> Optional[dict]:
    """Update a todo item."""
    existing = await get_todo(todo_id)
    if not existing:
        return None

    updates = []
    values = []

    if title is not None:
        updates.append("title = ?")
        values.append(title)
    if description is not None:
        updates.append("description = ?")
        values.append(description)
    if completed is not None:
        updates.append("completed = ?")
        values.append(completed)

    if not updates:
        return existing

    updates.append("updated_at = ?")
    values.append(datetime.now(timezone.utc).isoformat())
    values.append(todo_id)

    conn = get_connection()
    conn.execute(
        f"UPDATE todos SET {', '.join(updates)} WHERE id = ?",
        values,
    )
    conn.commit()

    return await get_todo(todo_id)


async def delete_todo(todo_id: int) -> bool:
    """Delete a todo item. Returns True if deleted."""
    conn = get_connection()
    cursor = conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    return cursor.rowcount > 0
