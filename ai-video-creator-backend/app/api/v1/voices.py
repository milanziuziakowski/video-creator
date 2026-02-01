"""Voice API endpoints for managing cloned voices."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models.user import User
from app.db.models.voice import Voice
from app.db.models.project import Project, ProjectStatus
from app.models.voice import (
    VoiceCreate,
    VoiceResponse,
    VoiceListResponse,
    AssignVoiceRequest,
)

router = APIRouter(prefix="/voices", tags=["voices"])


@router.get("/", response_model=VoiceListResponse)
async def list_voices(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VoiceListResponse:
    """List all cloned voices for the current user."""
    # Get total count
    count_query = select(func.count(Voice.id)).where(Voice.user_id == current_user.id)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get voices
    query = (
        select(Voice)
        .where(Voice.user_id == current_user.id)
        .order_by(Voice.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    voices = result.scalars().all()

    return VoiceListResponse(
        voices=[VoiceResponse.model_validate(v) for v in voices],
        total=total,
    )


@router.post("/", response_model=VoiceResponse, status_code=201)
async def create_voice(
    voice_data: VoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VoiceResponse:
    """Create a new voice record for an already cloned voice."""
    # Check if voice_id already exists
    existing_query = select(Voice).where(Voice.voice_id == voice_data.voice_id)
    existing_result = await db.execute(existing_query)
    existing = existing_result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="A voice with this voice_id already exists"
        )

    voice = Voice(
        user_id=current_user.id,
        voice_id=voice_data.voice_id,
        name=voice_data.name,
        description=voice_data.description,
    )
    db.add(voice)
    await db.commit()
    await db.refresh(voice)

    return VoiceResponse.model_validate(voice)


@router.get("/{voice_id}", response_model=VoiceResponse)
async def get_voice(
    voice_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VoiceResponse:
    """Get a specific voice by ID."""
    query = select(Voice).where(
        Voice.id == voice_id,
        Voice.user_id == current_user.id,
    )
    result = await db.execute(query)
    voice = result.scalar_one_or_none()

    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")

    return VoiceResponse.model_validate(voice)


@router.delete("/{voice_id}", status_code=204)
async def delete_voice(
    voice_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a voice record."""
    query = select(Voice).where(
        Voice.id == voice_id,
        Voice.user_id == current_user.id,
    )
    result = await db.execute(query)
    voice = result.scalar_one_or_none()

    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")

    await db.delete(voice)
    await db.commit()


@router.post("/assign", response_model=dict)
async def assign_voice_to_project(
    request: AssignVoiceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Assign an existing cloned voice to a project.
    
    This allows reusing a previously cloned voice without re-cloning.
    """
    # Verify the voice exists and belongs to the user
    voice_query = select(Voice).where(
        Voice.voice_id == request.voice_id,
        Voice.user_id == current_user.id,
    )
    voice_result = await db.execute(voice_query)
    voice = voice_result.scalar_one_or_none()

    if not voice:
        raise HTTPException(
            status_code=404,
            detail="Voice not found or does not belong to you"
        )

    # Verify the project exists and belongs to the user
    project_query = select(Project).where(
        Project.id == request.project_id,
        Project.user_id == current_user.id,
    )
    project_result = await db.execute(project_query)
    project = project_result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Update project with voice_id
    project.voice_id = request.voice_id
    if project.status == ProjectStatus.CREATED:
        project.status = ProjectStatus.MEDIA_UPLOADED
    
    await db.commit()

    return {"voice_id": request.voice_id, "project_id": request.project_id}
