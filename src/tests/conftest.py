"""Test configuration and fixtures."""

import pytest
from httpx import ASGITransport, AsyncClient

from todo_api import database
from todo_api.main import app


@pytest.fixture(autouse=True)
async def setup_database():
    """Set up clean database before each test."""
    # Close any existing connection
    database.close_connection()

    # Remove the database file if it exists
    db_path = database.DATABASE_PATH
    if db_path.exists():
        db_path.unlink()

    # Initialize fresh database
    await database.init_db()

    yield

    # Cleanup after test
    database.close_connection()
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
async def client():
    """Create test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
