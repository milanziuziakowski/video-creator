"""Project service for project CRUD operations."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.project import Project, ProjectStatus
from app.db.models.segment import Segment, SegmentStatus
from app.models.project import ProjectCreate, ProjectUpdate
from app.services.media_service import MediaService


class ProjectService:
    """Service for project management operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_projects(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Project], int]:
        """List projects for a user.

        Args:
            user_id: User ID
            skip: Number of items to skip
            limit: Maximum items to return

        Returns:
            Tuple of (projects list, total count)
        """
        # Get total count
        count_query = select(func.count(Project.id)).where(Project.user_id == user_id)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Get projects with segments
        query = (
            select(Project)
            .where(Project.user_id == user_id)
            .options(selectinload(Project.segments))
            .order_by(Project.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        projects = list(result.scalars().all())

        return projects, total

    async def get_project(
        self,
        project_id: str,
        user_id: str,
    ) -> Project | None:
        """Get a project by ID.

        Args:
            project_id: Project ID
            user_id: User ID (for ownership verification)

        Returns:
            Project if found and owned by user, None otherwise
        """
        query = (
            select(Project)
            .where(Project.id == project_id, Project.user_id == user_id)
            .options(selectinload(Project.segments))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_project(
        self,
        user_id: str,
        data: ProjectCreate,
    ) -> Project:
        """Create a new project.

        Args:
            user_id: User ID
            data: Project creation data

        Returns:
            Created project
        """
        # Calculate segment count
        segment_count = data.target_duration_sec // data.segment_len_sec

        project = Project(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=data.name,
            story_prompt=data.story_prompt,
            target_duration_sec=data.target_duration_sec,
            segment_len_sec=data.segment_len_sec,
            segment_count=segment_count,
            status=ProjectStatus.CREATED,
        )

        self.db.add(project)
        await self.db.flush()

        # Create empty segments
        for i in range(segment_count):
            segment = Segment(
                id=str(uuid.uuid4()),
                project_id=project.id,
                index=i,
                status=SegmentStatus.PENDING,
            )
            self.db.add(segment)

        await self.db.flush()

        # Reload with segments
        return await self.get_project(project.id, user_id)  # type: ignore

    async def update_project(
        self,
        project_id: str,
        user_id: str,
        data: ProjectUpdate,
    ) -> Project | None:
        """Update a project.

        Args:
            project_id: Project ID
            user_id: User ID
            data: Update data

        Returns:
            Updated project if found
        """
        project = await self.get_project(project_id, user_id)
        if not project:
            return None

        if data.name is not None:
            project.name = data.name
        if data.story_prompt is not None:
            project.story_prompt = data.story_prompt
        if data.target_duration_sec is not None:
            project.target_duration_sec = data.target_duration_sec
        if data.segment_len_sec is not None:
            project.segment_len_sec = data.segment_len_sec

        if data.target_duration_sec is not None or data.segment_len_sec is not None:
            project.segment_count = project.target_duration_sec // project.segment_len_sec

        await self.db.flush()
        return project

    async def delete_project(
        self,
        project_id: str,
        user_id: str,
    ) -> bool:
        """Delete a project and all associated data.

        Args:
            project_id: Project ID
            user_id: User ID

        Returns:
            True if deleted, False if not found
        """
        project = await self.get_project(project_id, user_id)
        if not project:
            return False

        await self.db.delete(project)
        await self.db.flush()
        return True

    async def update_project_status(
        self,
        project_id: str,
        status: ProjectStatus,
    ) -> None:
        """Update project status.

        Args:
            project_id: Project ID
            status: New status
        """
        query = select(Project).where(Project.id == project_id)
        result = await self.db.execute(query)
        project = result.scalar_one_or_none()

        if project:
            project.status = status
            await self.db.flush()

    async def set_voice_id(
        self,
        project_id: str,
        voice_id: str,
    ) -> None:
        """Set the cloned voice ID for a project.

        Args:
            project_id: Project ID
            voice_id: MiniMax voice ID
        """
        query = select(Project).where(Project.id == project_id)
        result = await self.db.execute(query)
        project = result.scalar_one_or_none()

        if project:
            project.voice_id = voice_id
            await self.db.flush()

    async def set_first_frame_url(
        self,
        project_id: str,
        url: str,
    ) -> None:
        """Set the first frame URL for a project.

        Args:
            project_id: Project ID
            url: URL to first frame image
        """
        query = select(Project).where(Project.id == project_id)
        result = await self.db.execute(query)
        project = result.scalar_one_or_none()

        if project:
            project.first_frame_url = url
            await self.db.flush()

    async def set_audio_sample_url(
        self,
        project_id: str,
        url: str,
    ) -> None:
        """Set the audio sample URL for a project.

        Args:
            project_id: Project ID
            url: URL to audio sample
        """
        query = select(Project).where(Project.id == project_id)
        result = await self.db.execute(query)
        project = result.scalar_one_or_none()

        if project:
            project.audio_sample_url = url
            await self.db.flush()

    async def finalize_project(
        self,
        project_id: str,
        user_id: str,
    ) -> Project | None:
        """Finalize a project - concatenate all segments.

        Args:
            project_id: Project ID
            user_id: User ID

        Returns:
            Updated project with final video URL
        """
        project = await self.get_project(project_id, user_id)
        if not project:
            return None

        # Check all segments are approved
        if not all(seg.status == SegmentStatus.SEGMENT_APPROVED for seg in project.segments):
            raise ValueError("Not all segments are approved")

        project.status = ProjectStatus.FINALIZING
        await self.db.flush()

        # Use media service to concatenate
        media_service = MediaService()
        final_video_url = await media_service.finalize_project_video(project)

        project.final_video_url = final_video_url
        project.status = ProjectStatus.COMPLETED
        await self.db.flush()

        return project
