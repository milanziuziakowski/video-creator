"""Generation API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models.user import User
from app.models.generation import (
    GeneratePlanRequest,
    GenerationStatusResponse,
    VideoPlanResponse,
)
from app.services.orchestrator_service import OrchestratorService

router = APIRouter(prefix="/generation", tags=["generation"])


@router.post("/plan", response_model=VideoPlanResponse)
async def generate_video_plan(
    request: GeneratePlanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VideoPlanResponse:
    """Generate AI video plan for a project."""
    service = OrchestratorService(db)

    try:
        plan = await service.generate_video_plan(
            project_id=request.project_id,
            user_id=current_user.id,
            story_prompt=request.story_prompt,
        )
        return plan
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice-clone")
async def clone_voice(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Clone voice from project's audio sample."""
    service = OrchestratorService(db)

    try:
        voice_id = await service.clone_voice(project_id, current_user.id)
        return {"voice_id": voice_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/segment/{segment_id}")
async def generate_segment(
    segment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Start segment generation (video + audio)."""
    service = OrchestratorService(db)

    try:
        task_id = await service.start_segment_generation(
            segment_id=segment_id,
            user_id=current_user.id,
        )
        return {"task_id": task_id, "status": "submitted"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}", response_model=GenerationStatusResponse)
async def get_generation_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
) -> GenerationStatusResponse:
    """Poll generation task status."""
    service = OrchestratorService(None)  # Stateless for polling

    try:
        status = await service.get_generation_status(task_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
