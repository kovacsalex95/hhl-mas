"""
Todo API - Todos Router

CRUD endpoints for Todo items.
"""

from fastapi import APIRouter, HTTPException

from database import get_db, utc_now
from models import Todo, TodoCreate, TodoUpdate

router = APIRouter()


@router.get("/", response_model=list[Todo])
async def list_todos():
    """List all Todo items."""
    db = await get_db()
    cursor = await db.execute("SELECT * FROM todos ORDER BY created_at DESC")
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


@router.get("/{todo_id}", response_model=Todo)
async def get_todo(todo_id: int):
    """Get a specific Todo item by ID."""
    db = await get_db()
    cursor = await db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Todo not found")
    return dict(row)


@router.post("/", response_model=Todo, status_code=201)
async def create_todo(todo: TodoCreate):
    """Create a new Todo item."""
    db = await get_db()
    now = utc_now()
    cursor = await db.execute(
        """
        INSERT INTO todos (title, description, completed, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (todo.title, todo.description, todo.completed, now, now),
    )
    await db.commit()

    cursor = await db.execute("SELECT * FROM todos WHERE id = ?", (cursor.lastrowid,))
    row = await cursor.fetchone()
    return dict(row)


@router.put("/{todo_id}", response_model=Todo)
async def update_todo(todo_id: int, todo: TodoUpdate):
    """Update an existing Todo item."""
    db = await get_db()

    cursor = await db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
    existing = await cursor.fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Todo not found")

    updates = []
    values = []
    if todo.title is not None:
        updates.append("title = ?")
        values.append(todo.title)
    if todo.description is not None:
        updates.append("description = ?")
        values.append(todo.description)
    if todo.completed is not None:
        updates.append("completed = ?")
        values.append(todo.completed)

    if updates:
        updates.append("updated_at = ?")
        values.append(utc_now())
        values.append(todo_id)

        await db.execute(
            f"UPDATE todos SET {', '.join(updates)} WHERE id = ?",
            values,
        )
        await db.commit()

    cursor = await db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
    row = await cursor.fetchone()
    return dict(row)


@router.delete("/{todo_id}", status_code=204)
async def delete_todo(todo_id: int):
    """Delete a Todo item."""
    db = await get_db()

    cursor = await db.execute("SELECT id FROM todos WHERE id = ?", (todo_id,))
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="Todo not found")

    await db.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    await db.commit()
