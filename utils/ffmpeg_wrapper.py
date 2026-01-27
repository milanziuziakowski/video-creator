"""FFmpeg wrapper utilities for media operations.

This module provides high-level wrappers around FFmpeg commands
for video/audio processing operations.
"""

import asyncio
import json
import logging
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class FFmpegError(Exception):
    """Raised when FFmpeg operation fails."""
    pass


async def run_ffmpeg_command(
    args: List[str],
    check: bool = True,
    capture_output: bool = True,
    timeout: Optional[float] = None,
) -> subprocess.CompletedProcess:
    """Run FFmpeg command asynchronously.
    
    Args:
        args: FFmpeg command arguments (without 'ffmpeg' prefix)
        check: Raise exception on non-zero exit code
        capture_output: Capture stdout/stderr
        timeout: Command timeout in seconds
        
    Returns:
        CompletedProcess with stdout/stderr
        
    Raises:
        FFmpegError: If command fails and check=True
    """
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'warning'] + args
    
    logger.debug(f"Running FFmpeg: {' '.join(cmd)}")
    
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE if capture_output else None,
            stderr=asyncio.subprocess.PIPE if capture_output else None,
        )
        
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        
        result = subprocess.CompletedProcess(
            args=cmd,
            returncode=proc.returncode,
            stdout=stdout,
            stderr=stderr
        )
        
        if check and result.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise FFmpegError(f"FFmpeg command failed: {error_msg}")
        
        return result
        
    except asyncio.TimeoutError:
        logger.error(f"FFmpeg command timed out after {timeout}s")
        raise FFmpegError(f"Command timed out after {timeout}s")
    except Exception as e:
        logger.error(f"FFmpeg command error: {e}")
        raise FFmpegError(f"Command error: {e}")


async def probe_media(media_path: str) -> Dict[str, Any]:
    """Probe media file for metadata using ffprobe.
    
    Args:
        media_path: Path to media file
        
    Returns:
        Dictionary with media metadata
    """
    cmd = [
        'ffprobe',
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        media_path
    ]
    
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise FFmpegError(f"ffprobe failed: {stderr.decode()}")
        
        data = json.loads(stdout.decode())
        return data
        
    except json.JSONDecodeError as e:
        raise FFmpegError(f"Failed to parse ffprobe output: {e}")
    except Exception as e:
        raise FFmpegError(f"Probe error: {e}")


async def extract_last_frame_impl(
    video_path: str,
    output_path: str,
) -> Dict[str, Any]:
    """Extract last frame from video.
    
    Args:
        video_path: Path to source video
        output_path: Path to save frame (JPEG)
        
    Returns:
        Dictionary with output_path and metadata
    """
    args = [
        '-sseof', '-1',  # Seek to 1 second before end
        '-i', video_path,
        '-update', '1',
        '-frames:v', '1',
        '-q:v', '2',  # High quality
        output_path,
        '-y'  # Overwrite
    ]
    
    await run_ffmpeg_command(args, timeout=30.0)
    
    return {
        'output_path': output_path,
        'status': 'extracted'
    }


async def concat_videos_impl(
    video_paths: List[str],
    output_path: str,
) -> Dict[str, Any]:
    """Concatenate multiple videos.
    
    Args:
        video_paths: List of video file paths
        output_path: Path to save concatenated video
        
    Returns:
        Dictionary with output_path and duration
    """
    # Create concat file list
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for video_path in video_paths:
            # Escape quotes and write file path
            escaped_path = str(Path(video_path).absolute()).replace("'", "'\\''")
            f.write(f"file '{escaped_path}'\n")
        concat_file = f.name
    
    try:
        args = [
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',  # Don't re-encode
            output_path,
            '-y'
        ]
        
        await run_ffmpeg_command(args, timeout=120.0)
        
        # Probe final duration
        probe_data = await probe_media(output_path)
        duration = float(probe_data.get('format', {}).get('duration', 0))
        
        return {
            'output_path': output_path,
            'total_duration_sec': duration,
            'video_count': len(video_paths),
            'status': 'concatenated'
        }
    finally:
        # Clean up temp file
        Path(concat_file).unlink(missing_ok=True)


async def concat_audios_impl(
    audio_paths: List[str],
    output_path: str,
) -> Dict[str, Any]:
    """Concatenate multiple audio files.
    
    Args:
        audio_paths: List of audio file paths
        output_path: Path to save concatenated audio
        
    Returns:
        Dictionary with output_path and duration
    """
    # Similar to concat_videos but for audio
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for audio_path in audio_paths:
            escaped_path = str(Path(audio_path).absolute()).replace("'", "'\\''")
            f.write(f"file '{escaped_path}'\n")
        concat_file = f.name
    
    try:
        args = [
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',
            output_path,
            '-y'
        ]
        
        await run_ffmpeg_command(args, timeout=120.0)
        
        probe_data = await probe_media(output_path)
        duration = float(probe_data.get('format', {}).get('duration', 0))
        
        return {
            'output_path': output_path,
            'total_duration_sec': duration,
            'audio_count': len(audio_paths),
            'status': 'concatenated'
        }
    finally:
        Path(concat_file).unlink(missing_ok=True)


async def mux_audio_video_impl(
    video_path: str,
    audio_path: str,
    output_path: str,
) -> Dict[str, Any]:
    """Mux audio and video streams.
    
    Args:
        video_path: Path to video file
        audio_path: Path to audio file
        output_path: Path to save muxed video
        
    Returns:
        Dictionary with output_path and duration
    """
    args = [
        '-i', video_path,
        '-i', audio_path,
        '-c:v', 'copy',  # Don't re-encode video
        '-c:a', 'aac',   # Encode audio to AAC
        '-b:a', '192k',  # Audio bitrate
        '-shortest',     # Match shortest stream
        output_path,
        '-y'
    ]
    
    await run_ffmpeg_command(args, timeout=120.0)
    
    probe_data = await probe_media(output_path)
    duration = float(probe_data.get('format', {}).get('duration', 0))
    
    return {
        'output_path': output_path,
        'final_duration_sec': duration,
        'status': 'muxed'
    }


async def normalize_audio_impl(
    audio_path: str,
    output_path: str,
    target_loudness_db: float = -23.0,
) -> Dict[str, Any]:
    """Normalize audio to target loudness.
    
    Args:
        audio_path: Path to source audio
        output_path: Path to save normalized audio
        target_loudness_db: Target loudness in LUFS
        
    Returns:
        Dictionary with output_path and measurements
    """
    # First pass: measure loudness
    measure_args = [
        '-i', audio_path,
        '-af', f'loudnorm=I={target_loudness_db}:print_format=json',
        '-f', 'null',
        '-'
    ]
    
    result = await run_ffmpeg_command(measure_args, check=False, timeout=60.0)
    
    # Second pass: apply normalization
    args = [
        '-i', audio_path,
        '-af', f'loudnorm=I={target_loudness_db}',
        output_path,
        '-y'
    ]
    
    await run_ffmpeg_command(args, timeout=60.0)
    
    return {
        'output_path': output_path,
        'target_loudness_db': target_loudness_db,
        'status': 'normalized'
    }
