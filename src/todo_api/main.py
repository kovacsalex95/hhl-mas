"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException

from .database import (
    create_todo,
    delete_todo,
    get_all_todos,
    get_todo,
    init_db,
    update_todo,
)
from .models import Todo, TodoCreate, TodoUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    yield


app = FastAPI(
    title="Todo API",
    description="A simple REST API for managing todo items",
    version="0.1.0",
    lifespan=lifespan,
)


def row_to_todo(row: dict) -> Todo:
    """Convert database row to Todo model."""
    return Todo(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        completed=bool(row["completed"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/todos", response_model=Todo, status_code=201)
async def create_todo_endpoint(todo: TodoCreate):
    """Create a new todo item."""
    row = await create_todo(
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
    )
    return row_to_todo(row)


@app.get("/todos", response_model=list[Todo])
async def list_todos():
    """List all todo items."""
    rows = await get_all_todos()
    return [row_to_todo(row) for row in rows]


@app.get("/todos/{todo_id}", response_model=Todo)
async def get_todo_endpoint(todo_id: int):
    """Get a specific todo item."""
    row = await get_todo(todo_id)
    if not row:
        raise HTTPException(status_code=404, detail="Todo not found")
    return row_to_todo(row)


@app.put("/todos/{todo_id}", response_model=Todo)
async def update_todo_endpoint(todo_id: int, todo: TodoUpdate):
    """Update a todo item."""
    row = await update_todo(
        todo_id=todo_id,
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Todo not found")
    return row_to_todo(row)


@app.delete("/todos/{todo_id}", status_code=204)
async def delete_todo_endpoint(todo_id: int):
    """Delete a todo item."""
    deleted = await delete_todo(todo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Todo not found")
    return None
