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


def url_to_file_path(url: str) -> Path:
    """Convert a URL path like /output/file.mp4 to absolute file path.
    
    Args:
        url: URL path starting with /output/, /temp/, or /uploads/
        
    Returns:
        Absolute Path to the file
    """
    if url.startswith("/output/"):
        return settings.storage_output / url[8:]  # Remove /output/
    elif url.startswith("/temp/"):
        return settings.storage_temp / url[6:]  # Remove /temp/
    elif url.startswith("/uploads/"):
        return settings.STORAGE_PATH / "uploads" / url[9:]  # Remove /uploads/
    else:
        # Assume it's already a path
        return Path(url)


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
        """Concatenate all segment videos with properly synced audio into final video.

        Each segment's audio is adjusted to match its video duration before muxing.
        Then all muxed segments are concatenated into the final video.

        Args:
            project: Project with all segments

        Returns:
            URL path to final video
        """
        muxed_segment_paths: list[Path] = []
        temp_files: list[Path] = []

        try:
            for segment in sorted(project.segments, key=lambda s: s.index):
                if not segment.video_url:
                    logger.warning(f"Segment {segment.id} has no video, skipping")
                    continue

                # Convert URL to file path
                video_path = url_to_file_path(segment.video_url)
                
                if not video_path.exists():
                    logger.error(f"Video file not found: {video_path}")
                    raise ValueError(f"Video file not found for segment {segment.index + 1}")

                if segment.audio_url:
                    audio_path = url_to_file_path(segment.audio_url)
                    
                    if not audio_path.exists():
                        logger.error(f"Audio file not found: {audio_path}")
                        raise ValueError(f"Audio file not found for segment {segment.index + 1}")

                    # Mux video with audio (audio will be adjusted to video length)
                    muxed_path = settings.storage_temp / f"muxed_{segment.id}.mp4"
                    await ffmpeg_wrapper.mux_segment_video_audio(
                        video_path, audio_path, muxed_path
                    )
                    muxed_segment_paths.append(muxed_path)
                    temp_files.append(muxed_path)
                    logger.info(f"Muxed segment {segment.index + 1}: {muxed_path}")
                else:
                    # No audio, use video as-is
                    muxed_segment_paths.append(video_path)
                    logger.info(f"Segment {segment.index + 1} has no audio, using video only")

            if not muxed_segment_paths:
                raise ValueError("No video segments to concatenate")

            # Concatenate all muxed segments
            final_path = settings.storage_output / f"final_{project.id}.mp4"
            await ffmpeg_wrapper.concat_videos(muxed_segment_paths, final_path)
            logger.info(f"Final video created: {final_path}")

            # Return as URL path
            return f"/output/final_{project.id}.mp4"

        finally:
            # Clean up temp muxed files
            for temp_file in temp_files:
                try:
                    temp_file.unlink(missing_ok=True)
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file {temp_file}: {e}")

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
