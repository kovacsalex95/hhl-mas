"""Unit tests for Todo API endpoints."""

import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_create_todo(client):
    """Test creating a todo."""
    response = await client.post(
        "/todos",
        json={"title": "Test Todo", "description": "A test item"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Todo"
    assert data["description"] == "A test item"
    assert data["completed"] is False
    assert "id" in data


@pytest.mark.asyncio
async def test_list_todos(client):
    """Test listing todos."""
    # Create a todo first
    await client.post("/todos", json={"title": "List Test"})

    response = await client.get("/todos")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_todo(client):
    """Test getting a specific todo."""
    # Create a todo first
    create_response = await client.post("/todos", json={"title": "Get Test"})
    todo_id = create_response.json()["id"]

    response = await client.get(f"/todos/{todo_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Get Test"


@pytest.mark.asyncio
async def test_get_todo_not_found(client):
    """Test getting a non-existent todo."""
    response = await client.get("/todos/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_todo(client):
    """Test updating a todo."""
    # Create a todo first
    create_response = await client.post("/todos", json={"title": "Update Test"})
    todo_id = create_response.json()["id"]

    response = await client.put(
        f"/todos/{todo_id}",
        json={"title": "Updated Title", "completed": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["completed"] is True


@pytest.mark.asyncio
async def test_delete_todo(client):
    """Test deleting a todo."""
    # Create a todo first
    create_response = await client.post("/todos", json={"title": "Delete Test"})
    todo_id = create_response.json()["id"]

    response = await client.delete(f"/todos/{todo_id}")
    assert response.status_code == 204

    # Verify it's gone
    get_response = await client.get(f"/todos/{todo_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_todo_not_found(client):
    """Test deleting a non-existent todo."""
    response = await client.delete("/todos/99999")
    assert response.status_code == 404
