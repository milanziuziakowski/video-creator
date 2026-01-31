"""End-to-end tests for the complete video creation workflow.

These tests simulate the full user journey from project creation to final video.
Run with: pytest tests/e2e/ -v --e2e
"""

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_workflow_project_creation(client: AsyncClient):
    """Test the complete project creation flow."""
    # Step 1: Create a project
    create_response = await client.post(
        "/api/v1/projects/",
        json={
            "name": "E2E Test Video",
            "storyPrompt": "A beautiful sunset over the ocean with waves crashing",
            "targetDurationSec": 30,
            "segmentDurationSec": 6,
        },
    )
    assert create_response.status_code == 201
    project = create_response.json()
    project_id = project["id"]

    assert project["name"] == "E2E Test Video"
    assert project["status"] == "created"

    # Step 2: Verify project is retrievable
    get_response = await client.get(f"/api/v1/projects/{project_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == project_id

    # Step 3: Verify project appears in list
    list_response = await client.get("/api/v1/projects/")
    assert list_response.status_code == 200
    projects = list_response.json()["projects"]
    assert any(p["id"] == project_id for p in projects)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_project_update_flow(client: AsyncClient):
    """Test project update functionality."""
    # Create project
    create_response = await client.post(
        "/api/v1/projects/",
        json={"name": "Update Test"},
    )
    project_id = create_response.json()["id"]

    # Update project
    update_response = await client.put(
        f"/api/v1/projects/{project_id}",
        json={
            "name": "Updated Name",
            "storyPrompt": "New story about space exploration",
            "targetDurationSec": 42,
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["name"] == "Updated Name"
    assert updated["storyPrompt"] == "New story about space exploration"
    assert updated["targetDurationSec"] == 42


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_project_delete_flow(client: AsyncClient):
    """Test project deletion functionality."""
    # Create project
    create_response = await client.post(
        "/api/v1/projects/",
        json={"name": "Delete Test"},
    )
    project_id = create_response.json()["id"]

    # Delete project
    delete_response = await client.delete(f"/api/v1/projects/{project_id}")
    assert delete_response.status_code == 204

    # Verify deletion
    get_response = await client.get(f"/api/v1/projects/{project_id}")
    assert get_response.status_code == 404


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_user_info_retrieval(client: AsyncClient):
    """Test user information endpoint."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 200
    user = response.json()

    assert "id" in user
    assert "email" in user
    assert "name" in user
    assert "createdAt" in user


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_pagination_flow(client: AsyncClient):
    """Test project listing pagination."""
    # Create multiple projects
    for i in range(5):
        await client.post(
            "/api/v1/projects/",
            json={"name": f"Pagination Test {i}"},
        )

    # Test pagination
    page1_response = await client.get("/api/v1/projects/", params={"skip": 0, "limit": 2})
    assert page1_response.status_code == 200
    page1 = page1_response.json()
    assert len(page1["projects"]) <= 2
    assert page1["total"] >= 5

    page2_response = await client.get("/api/v1/projects/", params={"skip": 2, "limit": 2})
    assert page2_response.status_code == 200
    page2 = page2_response.json()

    # Ensure different projects in each page
    page1_ids = {p["id"] for p in page1["projects"]}
    page2_ids = {p["id"] for p in page2["projects"]}
    assert page1_ids.isdisjoint(page2_ids)
