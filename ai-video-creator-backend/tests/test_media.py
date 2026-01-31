"""Tests for media upload endpoints."""

import io
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.models.project import Project, ProjectStatus
from app.db.models.segment import Segment, SegmentStatus


@pytest.fixture
async def project_for_upload(db_with_user: AsyncSession, test_user: User):
    """Create a project for upload testing."""
    project = Project(
        user_id=test_user.id,
        name="Upload Test",
        story_prompt="A story",
        target_duration_sec=60,
        status=ProjectStatus.CREATED,
    )
    db_with_user.add(project)
    await db_with_user.commit()
    await db_with_user.refresh(project)
    return project


@pytest.mark.asyncio
async def test_upload_first_frame(
    async_client: AsyncClient,
    project_for_upload,
):
    """Test uploading first frame image."""
    # Create a fake image file
    image_content = b"fake image content"
    
    with patch("app.services.media_service.MediaService.validate_image", new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = (True, None)
        
        with patch("app.services.media_service.MediaService.save_upload", new_callable=AsyncMock) as mock_save:
            from pathlib import Path
            mock_save.return_value = Path("/uploads/test.jpg")
            
            with patch("app.services.project_service.ProjectService.set_first_frame_url", new_callable=AsyncMock):
                response = await async_client.post(
                    f"/api/v1/media/upload/first-frame?project_id={project_for_upload.id}",
                    files={"file": ("test.jpg", io.BytesIO(image_content), "image/jpeg")},
                )
    
    assert response.status_code == 200
    data = response.json()
    assert "url" in data
    assert "filename" in data


@pytest.mark.asyncio
async def test_upload_first_frame_invalid_format(
    async_client: AsyncClient,
    project_for_upload,
):
    """Test uploading invalid file format."""
    image_content = b"invalid content"
    
    with patch("app.services.media_service.MediaService.validate_image", new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = (False, "Invalid image format")
        
        response = await async_client.post(
            f"/api/v1/media/upload/first-frame?project_id={project_for_upload.id}",
            files={"file": ("test.txt", io.BytesIO(image_content), "text/plain")},
        )
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_upload_audio_sample(
    async_client: AsyncClient,
    project_for_upload,
):
    """Test uploading audio sample."""
    audio_content = b"fake audio content"
    
    with patch("app.services.media_service.MediaService.validate_audio", new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = (True, None)
        
        with patch("app.services.media_service.MediaService.save_upload", new_callable=AsyncMock) as mock_save:
            from pathlib import Path
            mock_save.return_value = Path("/uploads/audio.mp3")
            
            with patch("app.services.project_service.ProjectService.set_audio_sample_url", new_callable=AsyncMock):
                with patch("app.services.project_service.ProjectService.update_project_status", new_callable=AsyncMock):
                    response = await async_client.post(
                        f"/api/v1/media/upload/audio?project_id={project_for_upload.id}",
                        files={"file": ("audio.mp3", io.BytesIO(audio_content), "audio/mpeg")},
                    )
    
    assert response.status_code == 200
    data = response.json()
    assert "url" in data


@pytest.mark.asyncio
async def test_upload_segment_frame(
    async_client: AsyncClient,
    db_with_user: AsyncSession,
    test_user: User,
):
    """Test uploading segment frame."""
    # Create project and segment
    project = Project(
        user_id=test_user.id,
        name="Test",
        status=ProjectStatus.PLANNED,
    )
    db_with_user.add(project)
    await db_with_user.flush()
    
    segment = Segment(
        project_id=project.id,
        index=0,
        video_prompt="Test",
        status=SegmentStatus.PROMPT_READY,
    )
    db_with_user.add(segment)
    await db_with_user.commit()
    await db_with_user.refresh(segment)
    
    image_content = b"fake frame content"
    
    with patch("app.services.media_service.MediaService.validate_image", new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = (True, None)
        
        with patch("app.services.media_service.MediaService.save_upload", new_callable=AsyncMock) as mock_save:
            from pathlib import Path
            mock_save.return_value = Path("/uploads/frame.jpg")
            
            response = await async_client.post(
                f"/api/v1/media/upload/segment-frame/{segment.id}?frame_type=first",
                files={"file": ("frame.jpg", io.BytesIO(image_content), "image/jpeg")},
            )
    
    assert response.status_code == 200
    data = response.json()
    assert data["frame_type"] == "first"


@pytest.mark.asyncio
async def test_download_final_video_not_available(
    async_client: AsyncClient,
    project_for_upload,
):
    """Test downloading final video when not available."""
    response = await async_client.get(f"/api/v1/media/download/{project_for_upload.id}/final")
    
    assert response.status_code == 404
