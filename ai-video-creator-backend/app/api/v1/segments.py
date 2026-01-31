"""Segments API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_current_user, get_db
from app.models.segment import SegmentUpdate, SegmentResponse
from app.db.models.user import User
from app.db.models.project import Project
from app.db.models.segment import Segment, SegmentStatus

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
    query = (
        select(Segment)
        .where(Segment.project_id == project_id)
        .order_by(Segment.index)
    )
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
