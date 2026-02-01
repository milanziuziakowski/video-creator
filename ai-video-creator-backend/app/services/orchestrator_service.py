"""Orchestrator service for video generation workflow."""

import base64
import uuid
import logging
import mimetypes
from typing import Optional
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.project import Project, ProjectStatus
from app.db.models.segment import Segment, SegmentStatus
from app.db.models.voice import Voice
from app.models.generation import VideoPlanResponse, GenerationStatusResponse, GenerationStatus
from app.agents import PlanGeneratorAgent, VideoStoryPlan, SegmentPrompt
from app.integrations import ffmpeg_wrapper
from app.integrations.minimax_client import MinimaxClient as MiniMaxClient
from app.config import settings

logger = logging.getLogger(__name__)


def url_to_base64_data_url(url: str) -> str:
    """Convert a local file URL to a base64 data URL.
    
    Args:
        url: Local URL like '/uploads/projects/xxx/file.jpg' or file path
        
    Returns:
        Base64 data URL like 'data:image/jpeg;base64,...'
    """
    # Handle local URLs (starting with /uploads, /output, or /temp)
    if url.startswith("/uploads/"):
        relative_path = url[len("/uploads/"):]
        file_path = settings.storage_uploads / relative_path
    elif url.startswith("/output/"):
        relative_path = url[len("/output/"):]
        file_path = settings.storage_output / relative_path
    elif url.startswith("/temp/"):
        relative_path = url[len("/temp/"):]
        file_path = settings.storage_temp / relative_path
    elif url.startswith(("http://", "https://")):
        # Already a public URL, return as-is
        return url
    elif url.startswith("data:"):
        # Already a data URL, return as-is
        return url
    else:
        # Assume it's a file path
        file_path = Path(url)
    
    if not file_path.exists():
        raise ValueError(f"File not found: {file_path}")
    
    # Read file and convert to base64
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    
    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if not mime_type:
        mime_type = "image/jpeg"  # Default to JPEG
    
    # Create data URL
    b64_data = base64.b64encode(file_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{b64_data}"


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
        voice_name: Optional[str] = None,
    ) -> str:
        """Clone voice from project's audio sample.

        Args:
            project_id: Project ID
            user_id: User ID
            voice_name: Optional name for the saved voice

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

        # Store audio path before any DB operations
        audio_path = Path(project.audio_sample_url)
        if not audio_path.exists():
            logger.error(f"Audio file not found at path: {audio_path}")
            raise ValueError(f"Audio file not found at path: {audio_path}")

        # Read audio file
        try:
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
        except Exception as e:
            logger.error(f"Failed to read audio file {audio_path}: {e}")
            raise ValueError(f"Failed to read audio file: {e}")

        # Update status to VOICE_CLONING
        project.status = ProjectStatus.VOICE_CLONING
        await self.db.flush()

        try:
            # Upload to MiniMax
            file_id = await self.minimax_client.upload_file(
                audio_bytes,
                audio_path.name,
                purpose="voice_clone",
            )

            # Clone voice
            voice_id = f"voice-{project_id[:8]}"
            await self.minimax_client.voice_clone(file_id, voice_id)

            # Update project with voice_id and status
            project.voice_id = voice_id
            project.status = ProjectStatus.MEDIA_UPLOADED
            
            # Save voice to voices table for reuse
            saved_voice_name = voice_name or f"Voice from {project.name}"
            voice_record = Voice(
                user_id=user_id,
                voice_id=voice_id,
                name=saved_voice_name,
                description=f"Cloned from project: {project.name}",
            )
            self.db.add(voice_record)
            
            await self.db.commit()
            
            return voice_id
            
        except Exception as e:
            logger.error(f"Voice cloning failed: {e}")
            # Rollback status change
            project.status = ProjectStatus.MEDIA_UPLOADED
            await self.db.commit()
            raise ValueError(f"Voice cloning failed: {e}")

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

        # Convert local URL to base64 data URL for MiniMax API
        try:
            first_frame_data_url = url_to_base64_data_url(first_frame_url)
        except ValueError as e:
            logger.error(f"Failed to convert first frame to base64: {e}")
            raise ValueError(f"First frame file not found: {first_frame_url}")

        # Generate video
        task_id = await self.minimax_client.generate_video(
            prompt=segment.video_prompt or "",
            first_frame_image=first_frame_data_url,
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
            audio_filename = f"audio_{segment.id}.mp3"
            audio_path = settings.storage_output / audio_filename
            with open(audio_path, "wb") as f:
                f.write(audio_bytes)

            # Store URL path (not file path) for frontend
            segment.audio_url = f"/output/{audio_filename}"
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
