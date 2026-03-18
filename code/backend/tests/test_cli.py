"""Tests for /api/v1/cli endpoints."""

import hashlib

import pytest
from httpx import AsyncClient

from app.models.api_key import ApiKey


@pytest.mark.asyncio
async def test_push_docs_returns_fully_serialized_documents(
    client: AsyncClient,
    db_session,
    test_project,
    test_user,
):
    raw_key = "sdd_test_cli_push_docs_key"
    api_key = ApiKey(
        project_id=test_project.id,
        name="CLI Test Key",
        key_prefix=raw_key[:12],
        key_hash=hashlib.sha256(raw_key.encode()).hexdigest(),
        created_by=test_user.id,
    )
    db_session.add(api_key)
    await db_session.commit()

    response = await client.post(
        "/api/v1/cli/push-docs",
        headers={"Authorization": f"Bearer {raw_key}"},
        json={
            "documents": [
                {
                    "path": "product/features/search.md",
                    "title": "Search",
                    "content": "# Search\n\nDocs content",
                },
                {
                    "path": "system/interfaces.md",
                    "title": "Interfaces",
                    "content": "# Interfaces\n\nInterface details",
                },
            ]
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["created"] == 2
    assert data["updated"] == 0
    assert len(data["documents"]) == 2
    for document in data["documents"]:
        assert document["created_at"]
        assert document["updated_at"]
        assert document["status"] == "synced"
