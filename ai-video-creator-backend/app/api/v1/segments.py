"""Segments API endpoints."""

import logging
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.config import settings
from app.db.models.project import Project
from app.db.models.segment import Segment, SegmentStatus
from app.db.models.user import User
from app.integrations.minimax_client import MiniMaxClient
from app.models.segment import SegmentResponse, SegmentUpdate
from app.services.media_service import MediaService, url_to_file_path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/segments", tags=["segments"])


async def verify_segment_ownership(
    segment_id: str,
    user_id: str,
    db: AsyncSession,
) -> Segment:
    """Verify user owns the segment's project."""
    query = select(Segment).where(Segment.id == segment_id)
    result = await db.execute(query)
    segment = result.scalar_one_or_none()

    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    # Verify ownership
    project_query = select(Project).where(
        Project.id == segment.project_id,
        Project.user_id == user_id,
    )
    project_result = await db.execute(project_query)
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Segment not found")

    return segment


@router.get("/project/{project_id}", response_model=list[SegmentResponse])
async def list_project_segments(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SegmentResponse]:
    """List all segments for a project."""
    # Verify project ownership
    project_query = select(Project).where(
        Project.id == project_id,
        Project.user_id == current_user.id,
    )
    project_result = await db.execute(project_query)
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    # Get segments
    query = select(Segment).where(Segment.project_id == project_id).order_by(Segment.index)
    result = await db.execute(query)
    segments = result.scalars().all()

    return [SegmentResponse.model_validate(seg) for seg in segments]


@router.get("/{segment_id}", response_model=SegmentResponse)
async def get_segment(
    segment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SegmentResponse:
    """Get segment by ID."""
    segment = await verify_segment_ownership(segment_id, current_user.id, db)
    return SegmentResponse.model_validate(segment)


@router.put("/{segment_id}", response_model=SegmentResponse)
async def update_segment(
    segment_id: str,
    data: SegmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SegmentResponse:
    """Update segment prompts."""
    segment = await verify_segment_ownership(segment_id, current_user.id, db)

    if data.video_prompt is not None:
        segment.video_prompt = data.video_prompt
    if data.narration_text is not None:
        segment.narration_text = data.narration_text
    if data.end_frame_prompt is not None:
        segment.end_frame_prompt = data.end_frame_prompt

    await db.flush()
    return SegmentResponse.model_validate(segment)


@router.delete("/{segment_id}/last-frame", response_model=SegmentResponse)
async def remove_last_frame(
    segment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SegmentResponse:
    """Remove the last frame from a segment."""
    segment = await verify_segment_ownership(segment_id, current_user.id, db)

    if segment.status == SegmentStatus.GENERATING:
        raise HTTPException(
            status_code=400,
            detail="Cannot modify segment while generating",
        )

    # Delete the file if it exists
    if segment.last_frame_url:
        try:
            from app.services.media_service import url_to_file_path

            file_path = url_to_file_path(segment.last_frame_url)
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.warning(f"Failed to delete last frame file: {e}")

    segment.last_frame_url = None
    await db.flush()

    return SegmentResponse.model_validate(segment)


@router.post("/{segment_id}/approve", response_model=SegmentResponse)
async def approve_segment(
    segment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SegmentResponse:
    """Approve segment prompt for generation."""
    segment = await verify_segment_ownership(segment_id, current_user.id, db)

    if segment.status != SegmentStatus.PROMPT_READY:
        raise HTTPException(
            status_code=400,
            detail="Segment must be in prompt_ready status to approve",
        )

    segment.approved = True
    segment.status = SegmentStatus.APPROVED
    await db.flush()

    return SegmentResponse.model_validate(segment)


@router.post("/{segment_id}/approve-video", response_model=SegmentResponse)
async def approve_generated_video(
    segment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SegmentResponse:
    """Approve generated video segment."""
    segment = await verify_segment_ownership(segment_id, current_user.id, db)

    if segment.status != SegmentStatus.GENERATED:
        raise HTTPException(
            status_code=400,
            detail="Segment must be in generated status to approve video",
        )

    segment.status = SegmentStatus.SEGMENT_APPROVED
    await db.flush()

    return SegmentResponse.model_validate(segment)


@router.post("/{segment_id}/check-complete", response_model=SegmentResponse)
async def check_segment_complete(
    segment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SegmentResponse:
    """Check if segment generation is complete (both video and audio).

    Polls MiniMax if video_task_id exists but no video_url.
    If both video_url and audio_url are present, updates status to GENERATED.
    Also extracts last frame and sets it as the next segment's first frame.
    """
    segment = await verify_segment_ownership(segment_id, current_user.id, db)

    # If we have a task ID but no video URL, poll MiniMax
    if (
        segment.video_task_id
        and not segment.video_url
        and segment.status == SegmentStatus.GENERATING
    ):
        try:
            client = MiniMaxClient()
            status = await client.query_video_status(segment.video_task_id)

            logger.info(f"MiniMax status for segment {segment_id}: {status}")

            if status.get("status") == "Success" and status.get("file_id"):
                # Video is ready, download it
                download_url = await client.retrieve_file(status["file_id"])

                # Download and save video
                import httpx

                async with httpx.AsyncClient(timeout=120.0) as http_client:
                    response = await http_client.get(download_url)
                    response.raise_for_status()

                    video_filename = f"video_{segment.id}.mp4"
                    video_path = Path(settings.storage_output) / video_filename
                    video_path.write_bytes(response.content)

                    segment.video_url = f"/output/{video_filename}"
                    logger.info(f"Video downloaded for segment {segment_id}: {segment.video_url}")

                    # Extract last frame and set it for the next segment
                    await _extract_and_propagate_last_frame(segment, db)

        except Exception as e:
            logger.error(f"Error polling MiniMax for segment {segment_id}: {e}")

    # If both video and audio are present, mark as generated
    if segment.video_url and segment.audio_url and segment.status == SegmentStatus.GENERATING:
        segment.status = SegmentStatus.GENERATED
        logger.info(f"Segment {segment_id} marked as GENERATED")
        await db.flush()

    return SegmentResponse.model_validate(segment)


async def _extract_and_propagate_last_frame(segment: Segment, db: AsyncSession) -> None:
    """Extract last frame from segment video and set it as next segment's first frame."""
    try:
        # Get the video file path
        if not segment.video_url:
            logger.warning(f"No video URL for segment {segment.id}")
            return

        # Convert URL to file path using helper
        video_path = url_to_file_path(segment.video_url)

        if not video_path.exists():
            logger.error(f"Video file not found: {video_path}")
            return

        logger.info(f"Extracting last frame from {video_path}")

        # Extract last frame
        media_service = MediaService()
        frame_filename = f"last_frame_{segment.id}.jpg"
        frame_path = await media_service.extract_last_frame(video_path, frame_filename)

        logger.info(f"Last frame extracted to {frame_path}")

        # Save as this segment's last frame
        segment.last_frame_url = f"/temp/{frame_filename}"

        # Find the next segment
        next_segment_query = select(Segment).where(
            Segment.project_id == segment.project_id, Segment.index == segment.index + 1
        )
        result = await db.execute(next_segment_query)
        next_segment = result.scalar_one_or_none()

        if next_segment:
            # Copy frame to next segment's first frame
            next_frame_filename = f"first_frame_{next_segment.id}.jpg"
            next_frame_path = settings.storage_temp / next_frame_filename
            shutil.copy(str(frame_path), str(next_frame_path))

            next_segment.first_frame_url = f"/temp/{next_frame_filename}"
            logger.info(
                f"Set first frame for segment {next_segment.id} (index {next_segment.index}) from segment {segment.id}"
            )
        else:
            logger.info(f"No next segment found after segment {segment.id} (index {segment.index})")

        await db.flush()
        logger.info(f"Frame propagation complete for segment {segment.id}")

    except Exception as e:
        logger.error(f"Error extracting/propagating last frame: {e}", exc_info=True)


@router.post("/{segment_id}/extract-last-frame", response_model=SegmentResponse)
async def extract_last_frame_to_next(
    segment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SegmentResponse:
    """Manually extract last frame from segment video and set as next segment's first frame.

    This is a manual trigger for the frame extraction that normally happens automatically.
    Useful when automatic extraction failed or when re-extracting is needed.
    """
    segment = await verify_segment_ownership(segment_id, current_user.id, db)

    if not segment.video_url:
        raise HTTPException(
            status_code=400,
            detail="Segment must have a video to extract last frame",
        )

    await _extract_and_propagate_last_frame(segment, db)

    # Refresh segment data to get updated last_frame_url
    await db.refresh(segment)

    return SegmentResponse.model_validate(segment)


@router.post("/{segment_id}/regenerate", response_model=SegmentResponse)
async def request_regenerate(
    segment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SegmentResponse:
    """Request segment regeneration."""
    segment = await verify_segment_ownership(segment_id, current_user.id, db)

    # Reset to approved state for regeneration
    segment.status = SegmentStatus.APPROVED
    segment.video_url = None
    segment.video_task_id = None
    await db.flush()

    return SegmentResponse.model_validate(segment)
