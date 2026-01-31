"""E2E tests for segment operations."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.project import Project, ProjectStatus
from app.db.models.segment import Segment, SegmentStatus


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_segment_list_empty(client: AsyncClient, db_session: AsyncSession, mock_user):
    """Test listing segments for a project with no segments."""
    # Create a project
    project = Project(
        name="Segment Test Project",
        user_id=mock_user.id,
        status=ProjectStatus.CREATED,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # List segments
    response = await client.get(f"/api/v1/segments/project/{project.id}")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_segment_crud_operations(client: AsyncClient, db_session: AsyncSession, mock_user):
    """Test segment CRUD operations."""
    # Create a project
    project = Project(
        name="Segment CRUD Test",
        user_id=mock_user.id,
        status=ProjectStatus.PLAN_READY,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Create segments manually (simulating plan generation)
    segment = Segment(
        project_id=project.id,
        index=0,
        video_prompt="A sunset over the ocean",
        narration_text="The sun sets peacefully over the calm ocean waters.",
        status=SegmentStatus.PROMPT_READY,
    )
    db_session.add(segment)
    await db_session.commit()
    await db_session.refresh(segment)

    # Get segment
    get_response = await client.get(f"/api/v1/segments/{segment.id}")
    assert get_response.status_code == 200
    segment_data = get_response.json()
    assert segment_data["videoPrompt"] == "A sunset over the ocean"

    # Update segment
    update_response = await client.put(
        f"/api/v1/segments/{segment.id}",
        json={
            "videoPrompt": "A vibrant sunset with dramatic clouds",
            "narrationText": "The sky explodes with color as the sun descends.",
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["videoPrompt"] == "A vibrant sunset with dramatic clouds"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_segment_approval_flow(client: AsyncClient, db_session: AsyncSession, mock_user):
    """Test segment approval workflow."""
    # Create project and segment
    project = Project(
        name="Approval Test",
        user_id=mock_user.id,
        status=ProjectStatus.PLAN_READY,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    segment = Segment(
        project_id=project.id,
        index=0,
        video_prompt="Test prompt",
        narration_text="Test narration",
        status=SegmentStatus.PROMPT_READY,
    )
    db_session.add(segment)
    await db_session.commit()
    await db_session.refresh(segment)

    # Approve segment
    approve_response = await client.post(f"/api/v1/segments/{segment.id}/approve")
    assert approve_response.status_code == 200
    approved = approve_response.json()
    assert approved["status"] == "approved"
    assert approved["approved"] is True


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_segment_regenerate_flow(client: AsyncClient, db_session: AsyncSession, mock_user):
    """Test segment regeneration flow."""
    # Create project and segment in generated state
    project = Project(
        name="Regenerate Test",
        user_id=mock_user.id,
        status=ProjectStatus.GENERATING,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    segment = Segment(
        project_id=project.id,
        index=0,
        video_prompt="Test prompt",
        narration_text="Test narration",
        status=SegmentStatus.GENERATED,
        video_url="/tmp/video.mp4",
        approved=True,
    )
    db_session.add(segment)
    await db_session.commit()
    await db_session.refresh(segment)

    # Request regeneration
    regen_response = await client.post(f"/api/v1/segments/{segment.id}/regenerate")
    assert regen_response.status_code == 200
    regenerated = regen_response.json()
    assert regenerated["status"] == "approved"
    assert regenerated["videoUrl"] is None
