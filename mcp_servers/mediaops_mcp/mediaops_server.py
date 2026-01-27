"""MediaOps MCP Server - FFmpeg-based Media Operations.

This server exposes deterministic media operations:
- extract_last_frame: Extract last frame from video
- concat_videos: Concatenate multiple videos
- concat_audios: Concatenate multiple audio files
- mux_audio_video: Mux audio and video into final video
- normalize_audio: Normalize audio levels
- probe_duration: Get duration of media file

All operations use FFmpeg and are deterministic (no ML/API keys required).
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp.server.fastmcp import FastMCP
from utils.ffmpeg_wrapper import (
    extract_last_frame_impl,
    concat_videos_impl,
    concat_audios_impl,
    mux_audio_video_impl,
    normalize_audio_impl,
    probe_media,
)

# Configure logging to stderr (never stdout for MCP)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("mediaops")


@mcp.tool()
async def extract_last_frame(
    video_path: str,
    output_path: str,
) -> dict:
    """Extract the last frame from a video file.
    
    Args:
        video_path: Path to source video file
        output_path: Path to save extracted frame (JPEG)
    
    Returns:
        Dict with output_path and metadata
        
    Note:
        Uses FFmpeg to extract frame without re-encoding.
    """
    logger.info(f"extract_last_frame: video_path={video_path}")
    
    try:
        result = await extract_last_frame_impl(video_path, output_path)
        logger.info(f"Frame extracted successfully: {output_path}")
        return result
    except Exception as e:
        logger.error(f"Failed to extract frame: {e}")
        return {
            "output_path": output_path,
            "status": "failed",
            "error": str(e)
        }


@mcp.tool()
async def concat_videos(
    video_paths: list[str],
    output_path: str,
) -> dict:
    """Concatenate multiple video files into one.
    
    Args:
        video_paths: List of source video file paths
        output_path: Path to save concatenated video
    
    Returns:
        Dict with output_path and total_duration_sec
        
    Note:
        Uses FFmpeg concat demuxer for fast concatenation.
        Assumes all videos have same codec, resolution, frame rate.
    """
    logger.info(f"concat_videos: {len(video_paths)} videos -> {output_path}")
    
    try:
        result = await concat_videos_impl(video_paths, output_path)
        logger.info(f"Videos concatenated successfully: {output_path}")
        return result
    except Exception as e:
        logger.error(f"Failed to concatenate videos: {e}")
        return {
            "output_path": output_path,
            "video_count": len(video_paths),
            "status": "failed",
            "error": str(e)
        }


@mcp.tool()
async def concat_audios(
    audio_paths: list[str],
    output_path: str,
) -> dict:
    """Concatenate multiple audio files into one.
    
    Args:
        audio_paths: List of source audio file paths
        output_path: Path to save concatenated audio
    
    Returns:
        Dict with output_path and total_duration_sec
    """
    try:
        result = await concat_audios_impl(audio_paths, output_path)
        logger.info(f"Audios concatenated successfully: {output_path}")
        return result
    except Exception as e:
        logger.error(f"Failed to concatenate audios: {e}")
        return {
            "output_path": output_path,
            "audio_count": len(audio_paths),
            "status": "failed",
            "error": str(e)
        }


@mcp.tool()
async def mux_audio_video(
    video_path: str,
    audio_path: str,
    output_path: str,
) -> dict:
    """Mux audio and video streams into final video file.
    
    Args:
        video_path: Path to video file (video stream only)
        audio_path: Path to audio file (audio stream only)
        output_path: Path to save final muxed video
    
    Returns:
        Dict with output_path and final_duration_sec
        
    Note:
        Uses FFmpeg to mux without re-encoding (fast operation).
    """
    try:
        result = await mux_audio_video_impl(video_path, audio_path, output_path)
        logger.info(f"Audio and video muxed successfully: {output_path}")
        return result
    except Exception as e:
        logger.error(f"Failed to mux audio/video: {e}")
        return {
            "output_path": output_path,
            "status": "failed",
            "error": str(e)
        }


@mcp.tool()
async def normalize_audio(
    audio_path: str,
    output_path: str,
    target_loudness_db: float = -23.0,
) -> dict:
    """Normalize audio levels to target loudness (LUFS).
    
    Args:
        audio_path: Path to source audio file
        output_path: Path to save normalized audio
        target_loudness_db: Target loudness in LUFS (default: -23.0 for streaming)
    
    Returns:
        Dict with output_path and loudness measurements
    """
    try:
        result = await normalize_audio_impl(audio_path, output_path, target_loudness_db)
        logger.info(f"Audio normalized successfully: {output_path}")
        return result
    except Exception as e:
        logger.error(f"Failed to normalize audio: {e}")
        return {
            "output_path": output_path,
            "target_loudness_db": target_loudness_db,
            "status": "failed",
            "error": str(e)
        }


@mcp.tool()
async def probe_duration(media_path: str) -> dict:
    """Get duration and metadata of a media file.
    
    Args:
        media_path: Path to media file (video or audio)
    
    Returns:
        Dict with duration_sec and format metadata
    """
    try:
        probe_data = await probe_media(media_path)
        
        format_info = probe_data.get('format', {})
        streams = probe_data.get('streams', [])
        
        video_codec = None
        audio_codec = None
        
        for stream in streams:
            if stream.get('codec_type') == 'video':
                video_codec = stream.get('codec_name')
            elif stream.get('codec_type') == 'audio':
                audio_codec = stream.get('codec_name')
        
        return {
            "media_path": media_path,
            "duration_sec": float(format_info.get('duration', 0)),
            "format": format_info.get('format_name', 'unknown'),
            "video_codec": video_codec,
            "audio_codec": audio_codec,
            "status": "probed"
        }
    except Exception as e:
        logger.error(f"Failed to probe media: {e}")
        return {
            "media_path": media_path,
            "status": "failed",
            "error": str(e)
        }


def main():
    """Run the MCP server."""
    logger.info("Starting MediaOps MCP Server")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
