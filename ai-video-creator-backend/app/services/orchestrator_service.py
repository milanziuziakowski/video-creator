"""Orchestrator service for video generation workflow."""

import uuid
import logging
from typing import Optional
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.project import Project, ProjectStatus
from app.db.models.segment import Segment, SegmentStatus
from app.models.generation import VideoPlanResponse, GenerationStatusResponse, GenerationStatus
from app.agents import PlanGeneratorAgent, VideoStoryPlan, SegmentPrompt
from app.integrations import ffmpeg_wrapper
from app.integrations.minimax_client import MinimaxClient as MiniMaxClient
from app.config import settings

logger = logging.getLogger(__name__)


class OrchestratorService:
    """Service for orchestrating video generation workflow."""

    def __init__(self, db: Optional[AsyncSession]):
        self.db = db
        self.plan_agent = PlanGeneratorAgent()
        self.minimax_client = MiniMaxClient()

    async def generate_video_plan(
        self,
        project_id: str,
        user_id: str,
        story_prompt: str,
    ) -> VideoPlanResponse:
        """Generate AI video plan for a project.

        Args:
            project_id: Project ID
            user_id: User ID
            story_prompt: Story description

        Returns:
            Generated video plan
        """
        if not self.db:
            raise ValueError("Database session required")

        # Get project
        query = select(Project).where(Project.id == project_id, Project.user_id == user_id)
        result = await self.db.execute(query)
        project = result.scalar_one_or_none()

        if not project:
            raise ValueError("Project not found")

        # Update status
        project.status = ProjectStatus.PLAN_GENERATING
        project.story_prompt = story_prompt
        await self.db.flush()

        # Generate plan using OpenAI
        plan_result = await self.plan_agent.generate_plan(
            story_prompt=story_prompt,
            segment_count=project.segment_count,
            segment_duration=project.segment_len_sec,
        )

        plan_segments: list[SegmentPrompt | dict]
        if isinstance(plan_result, VideoStoryPlan):
            title = plan_result.title
            continuity_notes = plan_result.continuity_notes
            plan_segments = list(plan_result.segments)
        elif isinstance(plan_result, dict):
            title = plan_result.get("title", "Untitled")
            continuity_notes = plan_result.get("continuity_notes", "")
            plan_segments = list(plan_result.get("segments", []))
        else:
            raise ValueError("Invalid plan response")

        # Update segments with generated prompts
        segments_query = (
            select(Segment)
            .where(Segment.project_id == project_id)
            .order_by(Segment.index)
        )
        segments_result = await self.db.execute(segments_query)
        segments = list(segments_result.scalars().all())

        for index, (segment, prompt) in enumerate(zip(segments, plan_segments)):
            if isinstance(prompt, SegmentPrompt):
                segment.video_prompt = prompt.video_prompt
                segment.narration_text = prompt.narration_text
                segment.end_frame_prompt = prompt.end_frame_prompt
            else:
                segment.video_prompt = prompt.get("video_prompt")
                segment.narration_text = prompt.get("narration_text")
                segment.end_frame_prompt = prompt.get("end_frame_prompt")

            segment.status = SegmentStatus.PROMPT_READY

        project.status = ProjectStatus.PLAN_READY
        await self.db.flush()

        return VideoPlanResponse(
            title=title,
            segments=[
                {
                    "segment_index": (
                        s.segment_index if isinstance(s, SegmentPrompt) else i
                    ),
                    "video_prompt": (
                        s.video_prompt if isinstance(s, SegmentPrompt) else s.get("video_prompt")
                    ),
                    "narration_text": (
                        s.narration_text if isinstance(s, SegmentPrompt) else s.get("narration_text")
                    ),
                    "end_frame_prompt": (
                        s.end_frame_prompt if isinstance(s, SegmentPrompt) else s.get("end_frame_prompt")
                    ),
                }
                for i, s in enumerate(plan_segments)
            ],
            continuity_notes=continuity_notes,
        )

    async def clone_voice(
        self,
        project_id: str,
        user_id: str,
    ) -> str:
        """Clone voice from project's audio sample.

        Args:
            project_id: Project ID
            user_id: User ID

        Returns:
            Cloned voice ID
        """
        if not self.db:
            raise ValueError("Database session required")

        # Get project
        query = select(Project).where(Project.id == project_id, Project.user_id == user_id)
        result = await self.db.execute(query)
        project = result.scalar_one_or_none()

        if not project:
            raise ValueError("Project not found")

        if not project.audio_sample_url:
            raise ValueError("No audio sample uploaded")

        project.status = ProjectStatus.VOICE_CLONING
        await self.db.flush()

        # Read audio file
        audio_path = Path(project.audio_sample_url)
        if not audio_path.exists():
            raise ValueError("Audio file not found")

        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        # Upload to MiniMax
        file_id = await self.minimax_client.upload_file(
            audio_bytes,
            audio_path.name,
            purpose="voice_clone",
        )

        # Clone voice
        voice_id = f"voice-{project_id[:8]}"
        await self.minimax_client.voice_clone(file_id, voice_id)

        # Update project
        project.voice_id = voice_id
        project.status = ProjectStatus.PLAN_READY
        await self.db.flush()

        return voice_id

    async def start_segment_generation(
        self,
        segment_id: str,
        user_id: str,
    ) -> str:
        """Start generation for a segment.

        Args:
            segment_id: Segment ID
            user_id: User ID

        Returns:
            Task ID for polling
        """
        if not self.db:
            raise ValueError("Database session required")

        # Get segment with project
        query = select(Segment).where(Segment.id == segment_id)
        result = await self.db.execute(query)
        segment = result.scalar_one_or_none()

        if not segment:
            raise ValueError("Segment not found")

        # Verify user ownership
        project_query = select(Project).where(
            Project.id == segment.project_id, Project.user_id == user_id
        )
        project_result = await self.db.execute(project_query)
        project = project_result.scalar_one_or_none()

        if not project:
            raise ValueError("Project not found or not owned by user")

        # Check segment is approved
        if not segment.approved:
            raise ValueError("Segment must be approved before generation")

        # Update status
        segment.status = SegmentStatus.GENERATING
        project.status = ProjectStatus.GENERATING
        await self.db.flush()

        # Determine first frame
        first_frame_url = segment.first_frame_url or project.first_frame_url
        if not first_frame_url:
            raise ValueError("No first frame available")

        # Generate video
        task_id = await self.minimax_client.generate_video(
            prompt=segment.video_prompt or "",
            first_frame_image=first_frame_url,
            duration=project.segment_len_sec,
            resolution="768P",
        )

        segment.video_task_id = task_id
        await self.db.flush()

        # Start audio generation in background if voice cloned
        if project.voice_id and segment.narration_text:
            await self._generate_segment_audio(segment, project.voice_id)

        return task_id

    async def _generate_segment_audio(
        self,
        segment: Segment,
        voice_id: str,
    ) -> None:
        """Generate audio for a segment.

        Args:
            segment: Segment to generate audio for
            voice_id: Cloned voice ID
        """
        if not segment.narration_text:
            return

        try:
            audio_bytes = await self.minimax_client.text_to_audio(
                text=segment.narration_text,
                voice_id=voice_id,
            )

            # Save audio file
            audio_path = settings.storage_output / f"audio_{segment.id}.mp3"
            with open(audio_path, "wb") as f:
                f.write(audio_bytes)

            segment.audio_url = str(audio_path)
            if self.db:
                await self.db.flush()

        except Exception as e:
            logger.error(f"Audio generation failed for segment {segment.id}: {e}")

    async def get_generation_status(self, task_id: str) -> GenerationStatusResponse:
        """Get status of a generation task.

        Args:
            task_id: Task ID from MiniMax

        Returns:
            Generation status
        """
        try:
            status = await self.minimax_client.query_video_status(task_id)

            if status["status"] == "Success":
                download_url = await self.minimax_client.retrieve_file(status["file_id"])
                return GenerationStatusResponse(
                    task_id=task_id,
                    status=GenerationStatus.SUCCESS,
                    file_id=status["file_id"],
                    download_url=download_url,
                )
            elif status["status"] == "Fail":
                return GenerationStatusResponse(
                    task_id=task_id,
                    status=GenerationStatus.FAIL,
                    error="Video generation failed",
                )
            else:
                return GenerationStatusResponse(
                    task_id=task_id,
                    status=GenerationStatus.PROCESSING,
                )

        except Exception as e:
            logger.error(f"Error checking generation status: {e}")
            return GenerationStatusResponse(
                task_id=task_id,
                status=GenerationStatus.FAIL,
                error=str(e),
            )

    async def complete_segment_generation(
        self,
        segment_id: str,
        video_url: str,
    ) -> None:
        """Mark segment generation as complete.

        Args:
            segment_id: Segment ID
            video_url: URL to generated video
        """
        if not self.db:
            raise ValueError("Database session required")

        query = select(Segment).where(Segment.id == segment_id)
        result = await self.db.execute(query)
        segment = result.scalar_one_or_none()

        if segment:
            segment.video_url = video_url
            segment.status = SegmentStatus.GENERATED
            await self.db.flush()
