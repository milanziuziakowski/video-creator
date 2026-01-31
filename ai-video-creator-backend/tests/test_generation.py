"""Tests for generation endpoints."""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.models.project import Project, ProjectStatus
from app.db.models.segment import Segment, SegmentStatus


@pytest.fixture
async def project_for_generation(
    db_with_user: AsyncSession,
    test_user: User,
    tmp_path,
):
    """Create a project ready for generation."""
    audio_path = tmp_path / "audio.mp3"
    audio_path.write_bytes(b"fake audio content")
    project = Project(
        user_id=test_user.id,
        name="Generation Test",
        story_prompt="A story about adventure",
        target_duration_sec=60,
        status=ProjectStatus.MEDIA_UPLOADED,
        first_frame_url="/path/to/first_frame.jpg",
        audio_sample_url=str(audio_path),
    )
    db_with_user.add(project)
    await db_with_user.commit()
    await db_with_user.refresh(project)
    return project


@pytest.mark.asyncio
async def test_generate_plan(
    async_client: AsyncClient,
    project_for_generation,
    mock_plan_generator,
):
    """Test generating video plan."""
    with patch("app.services.orchestrator_service.PlanGeneratorAgent", return_value=mock_plan_generator):
        response = await async_client.post(
            "/api/v1/generation/plan",
            json={
                "projectId": project_for_generation.id,
                "storyPrompt": "A story about adventure",
            },
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "segments" in data
    assert len(data["segments"]) == 2


@pytest.mark.asyncio
async def test_generate_plan_project_not_found(async_client: AsyncClient, db_with_user: AsyncSession):
    """Test generating plan for non-existent project."""
    response = await async_client.post(
        "/api/v1/generation/plan",
        json={
            "projectId": "nonexistent",
            "storyPrompt": "A story",
        },
    )
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_clone_voice(
    async_client: AsyncClient,
    project_for_generation,
    mock_minimax_client,
):
    """Test voice cloning."""
    with patch("app.services.orchestrator_service.MiniMaxClient", return_value=mock_minimax_client):
        response = await async_client.post(
            f"/api/v1/generation/voice-clone?project_id={project_for_generation.id}"
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "voice_id" in data


@pytest.mark.asyncio
async def test_generate_segment(
    async_client: AsyncClient,
    db_with_user: AsyncSession,
    test_user: User,
    mock_minimax_client,
):
    """Test segment generation."""
    # Create project with voice
    project = Project(
        user_id=test_user.id,
        name="Test",
        status=ProjectStatus.PLANNED,
        voice_id="voice-123",
        first_frame_url="/path/to/frame.jpg",
    )
    db_with_user.add(project)
    await db_with_user.flush()
    
    # Create approved segment
    segment = Segment(
        project_id=project.id,
        index=0,
        video_prompt="Test prompt",
        narration_text="Test narration",
        status=SegmentStatus.APPROVED,
        first_frame_url="/path/to/first.jpg",
        approved=True,
    )
    db_with_user.add(segment)
    await db_with_user.commit()
    await db_with_user.refresh(segment)
    
    with patch("app.services.orchestrator_service.MiniMaxClient", return_value=mock_minimax_client):
        response = await async_client.post(f"/api/v1/generation/segment/{segment.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "submitted"


@pytest.mark.asyncio
async def test_get_generation_status(
    async_client: AsyncClient,
    mock_minimax_client,
):
    """Test getting generation status."""
    with patch("app.services.orchestrator_service.MiniMaxClient", return_value=mock_minimax_client):
        response = await async_client.get("/api/v1/generation/status/task-123")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
