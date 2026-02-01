"""FFmpeg wrapper for media operations."""

import asyncio
import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

# Thread pool for running subprocess commands (Windows compatibility)
_executor = ThreadPoolExecutor(max_workers=4)


class FFmpegWrapper:
    """Wrapper for FFmpeg operations."""

    def __init__(self, ffmpeg_path: str = "ffmpeg", ffprobe_path: str = "ffprobe"):
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path

    def _run_command_sync(self, cmd: list[str]) -> tuple[str, str]:
        """Run a command synchronously (for use in thread pool).

        Args:
            cmd: Command and arguments

        Returns:
            Tuple of (stdout, stderr)
        """
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            logger.error(f"FFmpeg command failed: {result.stderr}")
            raise Exception(f"FFmpeg error: {result.stderr}")

        return result.stdout, result.stderr

    async def _run_command(self, cmd: list[str]) -> tuple[str, str]:
        """Run a command asynchronously using thread pool (Windows compatible).

        Args:
            cmd: Command and arguments

        Returns:
            Tuple of (stdout, stderr)
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._run_command_sync, cmd)

    async def extract_last_frame(
        self,
        video_path: Path,
        output_path: Path,
    ) -> Path:
        """Extract the last frame from a video.

        Args:
            video_path: Path to input video
            output_path: Path for output image

        Returns:
            Path to extracted frame
        """
        # Get video duration first
        duration = await self.probe_duration(video_path)

        # Extract frame from near the end (0.1 seconds before end)
        time_position = max(0, duration - 0.1)

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-ss",
            str(time_position),
            "-i",
            str(video_path),
            "-vframes",
            "1",
            "-q:v",
            "2",
            "-update",
            "1",
            str(output_path),
        ]

        await self._run_command(cmd)
        return output_path

    async def extract_frame_at_time(
        self,
        video_path: Path,
        output_path: Path,
        time_seconds: float,
    ) -> Path:
        """Extract a frame at a specific time.

        Args:
            video_path: Path to input video
            output_path: Path for output image
            time_seconds: Time position in seconds

        Returns:
            Path to extracted frame
        """
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-ss",
            str(time_seconds),
            "-i",
            str(video_path),
            "-vframes",
            "1",
            "-q:v",
            "2",
            "-update",
            "1",
            str(output_path),
        ]

        await self._run_command(cmd)
        return output_path

    async def concat_videos(
        self,
        video_paths: list[Path],
        output_path: Path,
    ) -> Path:
        """Concatenate multiple videos into one.

        Args:
            video_paths: List of video file paths
            output_path: Path for output video

        Returns:
            Path to concatenated video
        """
        # Create a temp file list for FFmpeg
        list_file = settings.storage_temp / "concat_list.txt"
        with open(list_file, "w") as f:
            for video_path in video_paths:
                f.write(f"file '{video_path.absolute()}'\n")

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c",
            "copy",
            str(output_path),
        ]

        await self._run_command(cmd)
        list_file.unlink()  # Clean up temp file
        return output_path

    async def concat_audios(
        self,
        audio_paths: list[Path],
        output_path: Path,
    ) -> Path:
        """Concatenate multiple audio files into one.

        Args:
            audio_paths: List of audio file paths
            output_path: Path for output audio

        Returns:
            Path to concatenated audio
        """
        # Create a temp file list for FFmpeg
        list_file = settings.storage_temp / "audio_concat_list.txt"
        with open(list_file, "w") as f:
            for audio_path in audio_paths:
                f.write(f"file '{audio_path.absolute()}'\n")

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c",
            "copy",
            str(output_path),
        ]

        await self._run_command(cmd)
        list_file.unlink()  # Clean up temp file
        return output_path

    async def mux_audio_video(
        self,
        video_path: Path,
        audio_path: Path,
        output_path: Path,
    ) -> Path:
        """Combine video and audio into a single file.

        Args:
            video_path: Path to video file
            audio_path: Path to audio file
            output_path: Path for output file

        Returns:
            Path to muxed file
        """
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            str(output_path),
        ]

        await self._run_command(cmd)
        return output_path

    async def probe_duration(self, file_path: Path) -> float:
        """Get duration of a media file.

        Args:
            file_path: Path to media file

        Returns:
            Duration in seconds
        """
        cmd = [
            self.ffprobe_path,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(file_path),
        ]

        stdout, _ = await self._run_command(cmd)
        return float(stdout.strip())

    async def probe_video_info(self, file_path: Path) -> dict:
        """Get video file information.

        Args:
            file_path: Path to video file

        Returns:
            Dict with width, height, duration, codec
        """
        cmd = [
            self.ffprobe_path,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,codec_name,duration",
            "-of",
            "json",
            str(file_path),
        ]

        stdout, _ = await self._run_command(cmd)
        import json

        data = json.loads(stdout)

        if data.get("streams"):
            stream = data["streams"][0]
            return {
                "width": stream.get("width"),
                "height": stream.get("height"),
                "codec": stream.get("codec_name"),
                "duration": float(stream.get("duration", 0)),
            }
        return {}

    async def adjust_audio_duration(
        self,
        audio_path: Path,
        target_duration: float,
        output_path: Path,
    ) -> Path:
        """Adjust audio duration to match target duration.

        If audio is longer, it will be trimmed.
        If audio is shorter, it will be padded with silence.

        Args:
            audio_path: Path to input audio file
            target_duration: Target duration in seconds
            output_path: Path for output audio

        Returns:
            Path to adjusted audio file
        """
        current_duration = await self.probe_duration(audio_path)

        if abs(current_duration - target_duration) < 0.1:
            # Duration is close enough, just copy
            import shutil

            shutil.copy(audio_path, output_path)
            return output_path

        if current_duration > target_duration:
            # Trim audio
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-i",
                str(audio_path),
                "-t",
                str(target_duration),
                "-c:a",
                "libmp3lame",
                "-q:a",
                "2",
                str(output_path),
            ]
        else:
            # Pad with silence
            silence_duration = target_duration - current_duration
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-i",
                str(audio_path),
                "-af",
                f"apad=pad_dur={silence_duration}",
                "-t",
                str(target_duration),
                "-c:a",
                "libmp3lame",
                "-q:a",
                "2",
                str(output_path),
            ]

        await self._run_command(cmd)
        return output_path

    async def mux_segment_video_audio(
        self,
        video_path: Path,
        audio_path: Path,
        output_path: Path,
    ) -> Path:
        """Mux video and audio for a single segment, adjusting audio to video length.

        Args:
            video_path: Path to video file
            audio_path: Path to audio file
            output_path: Path for output file

        Returns:
            Path to muxed file
        """
        # Get video duration
        video_duration = await self.probe_duration(video_path)

        # Adjust audio to match video duration
        adjusted_audio = output_path.parent / f"adjusted_{output_path.stem}.mp3"
        await self.adjust_audio_duration(audio_path, video_duration, adjusted_audio)

        # Mux video with adjusted audio
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(adjusted_audio),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            str(output_path),
        ]

        await self._run_command(cmd)

        # Clean up adjusted audio
        adjusted_audio.unlink(missing_ok=True)

        return output_path


# Global instance
ffmpeg_wrapper = FFmpegWrapper()
