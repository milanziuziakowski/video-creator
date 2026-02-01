"""Media API endpoints for file uploads."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path

from app.api.deps import get_current_user, get_db
from app.config import settings
from app.db.models.user import User
from app.db.models.project import Project, ProjectStatus
from app.services.media_service import MediaService
from app.services.project_service import ProjectService

router = APIRouter(prefix="/media", tags=["media"])


def file_path_to_url(file_path: Path) -> str:
    """Convert a file system path to a URL path.
    
    Converts paths like 'storage/uploads/projects/xxx/file.jpg' 
    to '/uploads/projects/xxx/file.jpg'
    """
    # Get the path relative to storage_uploads
    try:
        relative_path = file_path.relative_to(settings.storage_uploads)
        return f"/uploads/{relative_path.as_posix()}"
    except ValueError:
        # If not in uploads, try output
        try:
            relative_path = file_path.relative_to(settings.storage_output)
            return f"/output/{relative_path.as_posix()}"
        except ValueError:
            # Return as-is if not in known directories
            return str(file_path)


@router.post("/upload/first-frame")
async def upload_first_frame(
    project_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Upload first frame image for a project."""
    # Verify project ownership
    project_query = select(Project).where(
        Project.id == project_id,
        Project.user_id == current_user.id,
    )
    result = await db.execute(project_query)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Read and validate file
    file_bytes = await file.read()
    media_service = MediaService()

    is_valid, error = await media_service.validate_image(file_bytes, file.filename or "image.jpg")
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    # Save file
    file_path = await media_service.save_upload(
        file_bytes,
        file.filename or "first_frame.jpg",
        subfolder=f"projects/{project_id}",
    )

    # Convert to URL
    url = file_path_to_url(file_path)

    # Update project with URL
    project_service = ProjectService(db)
    await project_service.set_first_frame_url(project_id, url)

    return {"url": url, "filename": file_path.name}


@router.post("/upload/audio")
async def upload_audio_sample(
    project_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Upload audio sample for voice cloning."""
    # Verify project ownership
    project_query = select(Project).where(
        Project.id == project_id,
        Project.user_id == current_user.id,
    )
    result = await db.execute(project_query)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Read and validate file
    file_bytes = await file.read()
    media_service = MediaService()

    is_valid, error = await media_service.validate_audio(file_bytes, file.filename or "audio.mp3")
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    # Save file
    file_path = await media_service.save_upload(
        file_bytes,
        file.filename or "audio_sample.mp3",
        subfolder=f"projects/{project_id}",
    )

    # Convert to URL
    url = file_path_to_url(file_path)

    # Update project with URL
    project_service = ProjectService(db)
    await project_service.set_audio_sample_url(project_id, url)

    # Update status to media_uploaded if both are present
    await db.refresh(project)
    if project.first_frame_url and project.audio_sample_url:
        await project_service.update_project_status(project_id, ProjectStatus.MEDIA_UPLOADED)

    return {"url": url, "filename": file_path.name}

    return {"url": str(file_path), "filename": file_path.name}


@router.post("/upload/segment-frame/{segment_id}")
async def upload_segment_frame(
    segment_id: str,
    frame_type: str,  # "first" or "last"
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Upload first or last frame for a segment."""
    from app.db.models.segment import Segment

    # Verify ownership
    segment_query = select(Segment).where(Segment.id == segment_id)
    segment_result = await db.execute(segment_query)
    segment = segment_result.scalar_one_or_none()

    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    project_query = select(Project).where(
        Project.id == segment.project_id,
        Project.user_id == current_user.id,
    )
    project_result = await db.execute(project_query)
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Segment not found")

    # Read and validate file
    file_bytes = await file.read()
    media_service = MediaService()

    is_valid, error = await media_service.validate_image(file_bytes, file.filename or "frame.jpg")
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    # Save file
    file_path = await media_service.save_upload(
        file_bytes,
        file.filename or f"{frame_type}_frame.jpg",
        subfolder=f"projects/{segment.project_id}/segments",
    )

    # Update segment
    url = file_path_to_url(file_path)
    if frame_type == "first":
        segment.first_frame_url = url
    elif frame_type == "last":
        segment.last_frame_url = url
    else:
        raise HTTPException(status_code=400, detail="frame_type must be 'first' or 'last'")

    await db.flush()

    return {"url": url, "filename": file_path.name, "frame_type": frame_type}


@router.get("/download/{project_id}/final")
async def download_final_video(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """Download final video for a project."""
    # Verify ownership
    project_query = select(Project).where(
        Project.id == project_id,
        Project.user_id == current_user.id,
    )
    result = await db.execute(project_query)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.final_video_url:
        raise HTTPException(status_code=404, detail="Final video not available")

    file_path = Path(project.final_video_url)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    return FileResponse(
        path=file_path,
        media_type="video/mp4",
        filename=f"{project.name.replace(' ', '_')}_final.mp4",
    )
