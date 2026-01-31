"""Media service for file handling and media operations."""

import uuid
import logging
from pathlib import Path
from typing import Optional
import aiofiles
import httpx

from app.config import settings
from app.integrations import ffmpeg_wrapper
from app.db.models.project import Project

logger = logging.getLogger(__name__)


class MediaService:
    """Service for media file operations."""

    async def save_upload(
        self,
        file_bytes: bytes,
        filename: str,
        subfolder: str = "",
    ) -> Path:
        """Save uploaded file to storage.

        Args:
            file_bytes: File content
            filename: Original filename
            subfolder: Optional subfolder within uploads

        Returns:
            Path to saved file
        """
        # Generate unique filename
        ext = Path(filename).suffix
        unique_name = f"{uuid.uuid4()}{ext}"

        # Create path
        if subfolder:
            folder = settings.storage_uploads / subfolder
        else:
            folder = settings.storage_uploads

        folder.mkdir(parents=True, exist_ok=True)
        file_path = folder / unique_name

        # Save file
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_bytes)

        return file_path

    async def download_file(
        self,
        url: str,
        filename: Optional[str] = None,
    ) -> Path:
        """Download file from URL to storage.

        Args:
            url: URL to download from
            filename: Optional filename (auto-generated if not provided)

        Returns:
            Path to downloaded file
        """
        if not filename:
            filename = f"{uuid.uuid4()}.mp4"

        file_path = settings.storage_temp / filename

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(url)
            response.raise_for_status()

            async with aiofiles.open(file_path, "wb") as f:
                await f.write(response.content)

        return file_path

    async def finalize_project_video(self, project: Project) -> str:
        """Concatenate all segment videos and audio into final video.

        Args:
            project: Project with all segments

        Returns:
            Path to final video
        """
        # Collect video files in order
        video_paths: list[Path] = []
        audio_paths: list[Path] = []

        for segment in sorted(project.segments, key=lambda s: s.index):
            if segment.video_url:
                video_path = Path(segment.video_url)
                if not video_path.exists():
                    # Download if URL
                    video_path = await self.download_file(
                        segment.video_url, f"segment_{segment.id}.mp4"
                    )
                video_paths.append(video_path)

            if segment.audio_url:
                audio_path = Path(segment.audio_url)
                if audio_path.exists():
                    audio_paths.append(audio_path)

        if not video_paths:
            raise ValueError("No video segments to concatenate")

        # Concatenate videos
        concat_video_path = settings.storage_output / f"concat_{project.id}.mp4"
        await ffmpeg_wrapper.concat_videos(video_paths, concat_video_path)

        # Concatenate audio if available
        if audio_paths:
            concat_audio_path = settings.storage_temp / f"concat_audio_{project.id}.mp3"
            await ffmpeg_wrapper.concat_audios(audio_paths, concat_audio_path)

            # Mux video and audio
            final_path = settings.storage_output / f"final_{project.id}.mp4"
            await ffmpeg_wrapper.mux_audio_video(
                concat_video_path, concat_audio_path, final_path
            )

            # Clean up
            concat_video_path.unlink()
            concat_audio_path.unlink()

            return str(final_path)

        return str(concat_video_path)

    async def extract_last_frame(
        self,
        video_path: Path,
        output_name: Optional[str] = None,
    ) -> Path:
        """Extract last frame from video.

        Args:
            video_path: Path to video file
            output_name: Optional output filename

        Returns:
            Path to extracted frame image
        """
        if not output_name:
            output_name = f"frame_{uuid.uuid4()}.jpg"

        output_path = settings.storage_temp / output_name
        return await ffmpeg_wrapper.extract_last_frame(video_path, output_path)

    async def validate_image(
        self,
        file_bytes: bytes,
        filename: str,
    ) -> tuple[bool, Optional[str]]:
        """Validate image file for MiniMax API requirements.

        Args:
            file_bytes: Image file bytes
            filename: Original filename

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file size
        max_size = settings.UPLOAD_MAX_SIZE_MB * 1024 * 1024
        if len(file_bytes) > max_size:
            return False, f"File too large. Max size: {settings.UPLOAD_MAX_SIZE_MB}MB"

        # Check extension
        valid_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        ext = Path(filename).suffix.lower()
        if ext not in valid_extensions:
            return False, f"Invalid format. Allowed: {', '.join(valid_extensions)}"

        return True, None

    async def validate_audio(
        self,
        file_bytes: bytes,
        filename: str,
    ) -> tuple[bool, Optional[str]]:
        """Validate audio file for voice cloning.

        Args:
            file_bytes: Audio file bytes
            filename: Original filename

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file size
        max_size = settings.UPLOAD_MAX_SIZE_MB * 1024 * 1024
        if len(file_bytes) > max_size:
            return False, f"File too large. Max size: {settings.UPLOAD_MAX_SIZE_MB}MB"

        # Check extension
        valid_extensions = {".mp3", ".wav", ".m4a", ".ogg"}
        ext = Path(filename).suffix.lower()
        if ext not in valid_extensions:
            return False, f"Invalid format. Allowed: {', '.join(valid_extensions)}"

        return True, None
