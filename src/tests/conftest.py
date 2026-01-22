"""
Test configuration and fixtures.
"""

import os
import pytest

# Use in-memory database for tests
os.environ["TEST_MODE"] = "1"

import database


@pytest.fixture(autouse=True)
async def setup_database():
    """Initialize database before each test, cleanup after."""
    # Use in-memory database for tests
    database.DB_PATH = ":memory:"
    await database.init_db()
    yield
    await database.close_db()
