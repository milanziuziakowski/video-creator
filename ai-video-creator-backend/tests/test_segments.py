"""Tests for segment endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.project import Project, ProjectStatus
from app.db.models.segment import Segment, SegmentStatus
from app.db.models.user import User


@pytest.fixture
async def project_with_segments(db_with_user: AsyncSession, test_user: User):
    """Create a project with segments."""
    project = Project(
        user_id=test_user.id,
        name="Test Project",
        story_prompt="A story",
        target_duration_sec=60,
        status=ProjectStatus.PLANNED,
    )
    db_with_user.add(project)
    await db_with_user.flush()

    segments = []
    for i in range(3):
        segment = Segment(
            project_id=project.id,
            index=i,
            video_prompt=f"Segment {i} video prompt",
            narration_text=f"Segment {i} narration",
            end_frame_prompt=f"Segment {i} end frame",
            duration_sec=6,
            status=SegmentStatus.PROMPT_READY,
        )
        db_with_user.add(segment)
        segments.append(segment)

    await db_with_user.commit()
    await db_with_user.refresh(project)
    for seg in segments:
        await db_with_user.refresh(seg)

    return project, segments


@pytest.mark.asyncio
async def test_list_project_segments(
    async_client: AsyncClient,
    project_with_segments,
):
    """Test listing segments for a project."""
    project, segments = project_with_segments

    response = await async_client.get(f"/api/v1/segments/project/{project.id}")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["index"] == 0
    assert data[1]["index"] == 1
    assert data[2]["index"] == 2


@pytest.mark.asyncio
async def test_get_segment(
    async_client: AsyncClient,
    project_with_segments,
):
    """Test getting a specific segment."""
    project, segments = project_with_segments
    segment = segments[0]

    response = await async_client.get(f"/api/v1/segments/{segment.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == segment.id
    assert data["videoPrompt"] == "Segment 0 video prompt"


@pytest.mark.asyncio
async def test_update_segment(
    async_client: AsyncClient,
    project_with_segments,
):
    """Test updating segment prompts."""
    project, segments = project_with_segments
    segment = segments[0]

    response = await async_client.put(
        f"/api/v1/segments/{segment.id}",
        json={
            "videoPrompt": "Updated video prompt",
            "narrationText": "Updated narration",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["videoPrompt"] == "Updated video prompt"
    assert data["narrationText"] == "Updated narration"


@pytest.mark.asyncio
async def test_approve_segment(
    async_client: AsyncClient,
    project_with_segments,
):
    """Test approving a segment."""
    project, segments = project_with_segments
    segment = segments[0]

    response = await async_client.post(f"/api/v1/segments/{segment.id}/approve")

    assert response.status_code == 200
    data = response.json()
    assert data["approved"] is True
    assert data["status"] == "approved"


@pytest.mark.asyncio
async def test_approve_segment_wrong_status(
    async_client: AsyncClient,
    db_with_user: AsyncSession,
    test_user: User,
):
    """Test approving segment in wrong status fails."""
    project = Project(
        user_id=test_user.id,
        name="Test Project",
        status=ProjectStatus.PLANNED,
    )
    db_with_user.add(project)
    await db_with_user.flush()

    segment = Segment(
        project_id=project.id,
        index=0,
        video_prompt="Test",
        status=SegmentStatus.GENERATING,  # Wrong status
    )
    db_with_user.add(segment)
    await db_with_user.commit()
    await db_with_user.refresh(segment)

    response = await async_client.post(f"/api/v1/segments/{segment.id}/approve")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_approve_video(
    async_client: AsyncClient,
    db_with_user: AsyncSession,
    test_user: User,
):
    """Test approving generated video."""
    project = Project(
        user_id=test_user.id,
        name="Test Project",
        status=ProjectStatus.PLANNED,
    )
    db_with_user.add(project)
    await db_with_user.flush()

    segment = Segment(
        project_id=project.id,
        index=0,
        video_prompt="Test",
        status=SegmentStatus.GENERATED,
        video_url="/path/to/video.mp4",
    )
    db_with_user.add(segment)
    await db_with_user.commit()
    await db_with_user.refresh(segment)

    response = await async_client.post(f"/api/v1/segments/{segment.id}/approve-video")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "segment_approved"


@pytest.mark.asyncio
async def test_request_regenerate(
    async_client: AsyncClient,
    db_with_user: AsyncSession,
    test_user: User,
):
    """Test requesting segment regeneration."""
    project = Project(
        user_id=test_user.id,
        name="Test Project",
        status=ProjectStatus.PLANNED,
    )
    db_with_user.add(project)
    await db_with_user.flush()

    segment = Segment(
        project_id=project.id,
        index=0,
        video_prompt="Test",
        status=SegmentStatus.GENERATED,
        video_url="/path/to/video.mp4",
        video_task_id="task-123",
    )
    db_with_user.add(segment)
    await db_with_user.commit()
    await db_with_user.refresh(segment)

    response = await async_client.post(f"/api/v1/segments/{segment.id}/regenerate")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["videoUrl"] is None
