"""
Todo API - Main Application Entry Point

M3 Real-world Pilot: A simple REST API for managing Todo items.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import init_db, close_db
from routers import todos


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown."""
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="Todo API",
    description="A simple REST API for managing Todo items (HMAS M3 Pilot)",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(todos.router, prefix="/todos", tags=["todos"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
