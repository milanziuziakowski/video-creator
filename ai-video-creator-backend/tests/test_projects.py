"""Tests for project endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.project import Project, ProjectStatus
from app.db.models.user import User


@pytest.mark.asyncio
async def test_create_project(async_client: AsyncClient, db_with_user: AsyncSession):
    """Test creating a new project."""
    response = await async_client.post(
        "/api/v1/projects/",
        json={
            "name": "Test Project",
            "storyPrompt": "A story about adventure",
            "targetDurationSec": 60,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["storyPrompt"] == "A story about adventure"
    assert data["targetDurationSec"] == 60
    assert data["status"] == "created"


@pytest.mark.asyncio
async def test_list_projects(
    async_client: AsyncClient, db_with_user: AsyncSession, test_user: User
):
    """Test listing user projects."""
    # Create a project first
    project = Project(
        user_id=test_user.id,
        name="Existing Project",
        story_prompt="A story",
        target_duration_sec=60,
        status=ProjectStatus.CREATED,
    )
    db_with_user.add(project)
    await db_with_user.commit()

    response = await async_client.get("/api/v1/projects/")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["projects"]) >= 1


@pytest.mark.asyncio
async def test_get_project(async_client: AsyncClient, db_with_user: AsyncSession, test_user: User):
    """Test getting a specific project."""
    project = Project(
        user_id=test_user.id,
        name="Test Project",
        story_prompt="A story",
        target_duration_sec=60,
        status=ProjectStatus.CREATED,
    )
    db_with_user.add(project)
    await db_with_user.commit()
    await db_with_user.refresh(project)

    response = await async_client.get(f"/api/v1/projects/{project.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project.id
    assert data["name"] == "Test Project"


@pytest.mark.asyncio
async def test_get_project_not_found(async_client: AsyncClient, db_with_user: AsyncSession):
    """Test getting a non-existent project."""
    response = await async_client.get("/api/v1/projects/nonexistent-id")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_project(
    async_client: AsyncClient, db_with_user: AsyncSession, test_user: User
):
    """Test updating a project."""
    project = Project(
        user_id=test_user.id,
        name="Original Name",
        story_prompt="Original story",
        target_duration_sec=60,
        status=ProjectStatus.CREATED,
    )
    db_with_user.add(project)
    await db_with_user.commit()
    await db_with_user.refresh(project)

    response = await async_client.put(
        f"/api/v1/projects/{project.id}",
        json={
            "name": "Updated Name",
            "storyPrompt": "Updated story",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["storyPrompt"] == "Updated story"


@pytest.mark.asyncio
async def test_delete_project(
    async_client: AsyncClient, db_with_user: AsyncSession, test_user: User
):
    """Test deleting a project."""
    project = Project(
        user_id=test_user.id,
        name="To Delete",
        story_prompt="Delete me",
        target_duration_sec=60,
        status=ProjectStatus.CREATED,
    )
    db_with_user.add(project)
    await db_with_user.commit()
    await db_with_user.refresh(project)

    response = await async_client.delete(f"/api/v1/projects/{project.id}")

    assert response.status_code == 204

    # Verify deletion
    get_response = await async_client.get(f"/api/v1/projects/{project.id}")
    assert get_response.status_code == 404
