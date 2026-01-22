#!/usr/bin/env python3
"""
API Validation Script

Quick validation of Todo API endpoints via direct ASGI calls.
"""

import asyncio
import sys

from httpx import ASGITransport, AsyncClient

sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

import database
from main import app


async def validate():
    """Run validation checks."""
    print("=== Todo API Validation ===\n")

    # Setup database
    database.DB_PATH = ":memory:"
    await database.init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        print("1. Health Check")
        r = await client.get("/health")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        print(f"   GET /health -> {r.status_code} OK")

        # 2. Create todo
        print("\n2. Create Todo")
        r = await client.post("/todos/", json={"title": "Buy groceries", "description": "Milk, eggs, bread"})
        assert r.status_code == 201, f"Expected 201, got {r.status_code}"
        todo = r.json()
        todo_id = todo["id"]
        print(f"   POST /todos/ -> {r.status_code} Created (id={todo_id})")

        # 3. List todos
        print("\n3. List Todos")
        r = await client.get("/todos/")
        assert r.status_code == 200
        assert len(r.json()) >= 1
        print(f"   GET /todos/ -> {r.status_code} OK ({len(r.json())} items)")

        # 4. Get specific todo
        print("\n4. Get Todo")
        r = await client.get(f"/todos/{todo_id}")
        assert r.status_code == 200
        assert r.json()["title"] == "Buy groceries"
        print(f"   GET /todos/{todo_id} -> {r.status_code} OK")

        # 5. Update todo
        print("\n5. Update Todo")
        r = await client.put(f"/todos/{todo_id}", json={"completed": True})
        assert r.status_code == 200
        assert r.json()["completed"] is True
        print(f"   PUT /todos/{todo_id} -> {r.status_code} OK (completed=True)")

        # 6. Delete todo
        print("\n6. Delete Todo")
        r = await client.delete(f"/todos/{todo_id}")
        assert r.status_code == 204
        print(f"   DELETE /todos/{todo_id} -> {r.status_code} No Content")

        # 7. Verify deletion
        print("\n7. Verify Deletion")
        r = await client.get(f"/todos/{todo_id}")
        assert r.status_code == 404
        print(f"   GET /todos/{todo_id} -> {r.status_code} Not Found (expected)")

    await database.close_db()
    print("\n=== All validations passed! ===")


if __name__ == "__main__":
    asyncio.run(validate())
