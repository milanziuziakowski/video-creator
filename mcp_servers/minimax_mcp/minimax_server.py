"""MiniMax MCP Server - FastMCP implementation.

This server exposes MiniMax API tools:
- voice_clone: Clone voice from audio sample
- text_to_audio: Generate audio from text using cloned voice
- text_to_image: Generate images from text prompts
- generate_video: Generate video (wrapper for FL2V)
- query_video_generation: Poll video generation status
"""

import io
import os
import logging
from pathlib import Path
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

# Configure logging to stderr (never stdout for MCP)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# MiniMax API Configuration
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
MINIMAX_API_BASE = "https://api.minimaxi.com/v1"
MINIMAX_TIMEOUT = 120.0  # 2 minutes for async operations

# Initialize FastMCP server
mcp = FastMCP("minimax")


# ============================================================================
# Helper Functions for API Communication
# ============================================================================

async def upload_audio_file(
    audio_bytes: bytes,
    filename: str,
    purpose: str = "voice_clone",
) -> Optional[str]:
    """Upload audio file to MiniMax and return file_id.
    
    Args:
        audio_bytes: Audio file bytes
        filename: Original filename (e.g., "sample.wav")
        purpose: Purpose of upload ("voice_clone", "prompt_audio", etc.)
    
    Returns:
        file_id string on success, None on failure
        
    Note:
        Follows official MiniMax API upload pattern.
        - Files must be 10s-5min for voice_clone, <8s for prompt_audio
        - Formats: mp3, m4a, wav
        - Max size: 20MB
    """
    if not MINIMAX_API_KEY:
        logger.error("MINIMAX_API_KEY not set in environment")
        return None
    
    try:
        # Validate audio size
        file_size_mb = len(audio_bytes) / (1024 * 1024)
        if file_size_mb > 20:
            logger.error(f"Audio file too large: {file_size_mb:.1f}MB (max 20MB)")
            return None
        
        # Prepare multipart form data
        files = {
            "file": (filename, io.BytesIO(audio_bytes), "audio/wav"),
            "purpose": (None, purpose),
        }
        
        headers = {
            "Authorization": f"Bearer {MINIMAX_API_KEY}"
        }
        
        # Upload file
        async with httpx.AsyncClient(timeout=MINIMAX_TIMEOUT) as client:
            logger.info(f"Uploading audio file: {filename} ({file_size_mb:.1f}MB) for {purpose}")
            
            response = await client.post(
                f"{MINIMAX_API_BASE}/files/upload",
                files=files,
                headers=headers
            )
            
            # Parse response
            if response.status_code != 200:
                logger.error(f"Upload failed: {response.status_code} - {response.text}")
                return None
            
            data = response.json()
            
            # Check API status
            if data.get("base_resp", {}).get("status_code") != 0:
                msg = data.get("base_resp", {}).get("status_msg", "Unknown error")
                logger.error(f"Upload API error: {msg}")
                return None
            
            # Extract file_id from response
            file_id = data.get("file", {}).get("file_id")
            if not file_id:
                logger.error("No file_id in upload response")
                return None
            
            logger.info(f"Audio uploaded successfully. file_id={file_id}")
            return file_id
    
    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        return None


async def call_video_generation_status(
    task_id: str,
    max_retries: int = 3,
    retry_delay: float = 1.0,
) -> Optional[dict]:
    """Query video generation status from MiniMax API.
    
    Args:
        task_id: Task ID from video generation request
        max_retries: Number of retry attempts on transient errors
        retry_delay: Initial delay between retries (exponential backoff)
    
    Returns:
        Dict with status, file_id (if ready), or error message on failure
        
    Note:
        Follows official MiniMax API pattern:
        - Status values: "submitted", "processing", "Success", "Fail"
        - Endpoint: GET /v1/query/video_generation?task_id={task_id}
        - Polling recommended every 10 seconds
        - File retrieval via file_id available after success
    """
    if not MINIMAX_API_KEY:
        logger.error("MINIMAX_API_KEY not set in environment")
        return None
    
    import asyncio
    
    retries = 0
    current_delay = retry_delay
    
    while retries < max_retries:
        try:
            headers = {
                "Authorization": f"Bearer {MINIMAX_API_KEY}",
                "Content-Type": "application/json"
            }
            
            params = {"task_id": task_id}
            
            logger.info(f"Querying video generation status: task_id={task_id}")
            
            async with httpx.AsyncClient(timeout=MINIMAX_TIMEOUT) as client:
                response = await client.get(
                    f"{MINIMAX_API_BASE}/query/video_generation",
                    params=params,
                    headers=headers
                )
            
            # Check HTTP status
            if response.status_code != 200:
                logger.warning(f"Status query returned {response.status_code}: {response.text}")
                
                # Don't retry on client errors (4xx)
                if 400 <= response.status_code < 500:
                    return {
                        "task_id": task_id,
                        "status": "failed",
                        "error": f"HTTP {response.status_code}: {response.text[:200]}"
                    }
                
                # Retry on server errors (5xx)
                retries += 1
                if retries < max_retries:
                    await asyncio.sleep(current_delay)
                    current_delay *= 2  # Exponential backoff
                    continue
                else:
                    return None
            
            # Parse response
            data = response.json()
            
            # Check API status code
            api_status = data.get("base_resp", {}).get("status_code")
            if api_status != 0:
                msg = data.get("base_resp", {}).get("status_msg", "Unknown API error")
                logger.error(f"Status query API error: {msg}")
                return None
            
            # Extract status
            status = data.get("status", "unknown")
            
            # Build response based on status
            if status == "Success":
                logger.info(f"Video generation completed: task_id={task_id}")
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "file_id": data.get("file_id"),  # Use for file retrieval
                    "video_url": None,  # Populated after file retrieval if needed
                }
            
            elif status == "Fail":
                error_msg = data.get("error_message", "Video generation failed")
                logger.error(f"Video generation failed: {error_msg}")
                return {
                    "task_id": task_id,
                    "status": "failed",
                    "error": error_msg,
                }
            
            elif status in ["submitted", "processing"]:
                logger.info(f"Video generation still {status}: task_id={task_id}")
                return {
                    "task_id": task_id,
                    "status": status,
                    "file_id": None,
                }
            
            else:
                logger.warning(f"Unknown status: {status}")
                return {
                    "task_id": task_id,
                    "status": status,
                    "file_id": data.get("file_id"),
                }
        
        except Exception as e:
            logger.error(f"Status query error: {e}", exc_info=True)
            retries += 1
            if retries < max_retries:
                await asyncio.sleep(current_delay)
                current_delay *= 2
                continue
            else:
                return None
    
    return None


async def call_voice_clone_api(
    file_id: str,
    voice_name: str,
    voice_id: Optional[str] = None,
    preview_text: Optional[str] = None,
    apply_noise_reduction: bool = True,
    apply_volume_normalization: bool = True,
) -> Optional[dict]:
    """Call MiniMax voice clone API.
    
    Args:
        file_id: ID of uploaded audio file (from upload_audio_file)
        voice_name: Friendly name for the cloned voice
        voice_id: Custom voice identifier (if None, auto-generate)
        preview_text: Optional preview text for demo audio generation
        apply_noise_reduction: Apply noise reduction preprocessing
        apply_volume_normalization: Normalize audio volume
    
    Returns:
        Dict with voice_id and status on success, None on failure
        
    Note:
        Follows official MiniMax API patterns:
        - voice_id must match: [a-zA-Z][a-zA-Z0-9\\-_]{7,255}
        - Cloned voices expire after 7 days (or sooner if not used)
        - Voice synthesis within 168 hours makes voice permanent
    """
    if not MINIMAX_API_KEY:
        logger.error("MINIMAX_API_KEY not set in environment")
        return None
    
    try:
        # Generate voice_id if not provided
        if not voice_id:
            # Use voice_name as base, ensure it starts with letter
            base = voice_name.replace(" ", "_").replace("-", "_")
            if not base or not base[0].isalpha():
                base = "voice_" + base
            voice_id = base[:256]  # Ensure reasonable length
            logger.info(f"Generated voice_id: {voice_id}")
        
        # Prepare request payload
        payload = {
            "file_id": file_id,
            "voice_id": voice_id,
            "need_noise_reduction": apply_noise_reduction,
            "need_volume_normalization": apply_volume_normalization,
        }
        
        # Add optional preview text if provided
        if preview_text:
            payload["text"] = preview_text[:1000]  # Max 1000 chars
            payload["model"] = "speech-2.6-turbo"  # Default turbo model for preview
        
        headers = {
            "Authorization": f"Bearer {MINIMAX_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Call voice clone API
        async with httpx.AsyncClient(timeout=MINIMAX_TIMEOUT) as client:
            logger.info(f"Calling voice_clone API: voice_id={voice_id}")
            
            response = await client.post(
                f"{MINIMAX_API_BASE}/voice_clone",
                json=payload,
                headers=headers
            )
            
            # Parse response
            if response.status_code != 200:
                logger.error(f"API call failed: {response.status_code} - {response.text}")
                return None
            
            data = response.json()
            
            # Check API status
            if data.get("base_resp", {}).get("status_code") != 0:
                msg = data.get("base_resp", {}).get("status_msg", "Unknown error")
                logger.error(f"Voice clone API error: {msg}")
                return None
            
            # Check content safety (optional)
            if data.get("input_sensitive"):
                logger.warning(f"Input flagged for content sensitivity (type: {data.get('input_sensitive_type')})")
            
            logger.info(f"Voice cloned successfully: {voice_id}")
            
            return {
                "voice_id": voice_id,
                "voice_name": voice_name,
                "status": "cloned",
                "demo_audio_url": data.get("demo_audio"),  # URL to preview audio if generated
            }
    
    except Exception as e:
        logger.error(f"Voice clone API error: {e}", exc_info=True)
        return None


# ============================================================================
# MCP Tools
# ============================================================================


@mcp.tool()
async def voice_clone(audio_bytes: bytes, voice_name: str) -> dict:
    """Clone a voice from audio sample and return voice_id.
    
    This tool implements the complete MiniMax voice cloning workflow:
    1. Upload audio file to MiniMax storage
    2. Call voice_clone API with uploaded file_id
    3. Return voice_id for use in text_to_audio()
    
    Args:
        audio_bytes: Audio sample bytes (WAV/MP3/M4A format)
        voice_name: Friendly name to assign to cloned voice
    
    Returns:
        Dict with:
            - voice_id: Unique identifier for cloned voice (use in text_to_audio)
            - voice_name: Friendly name of voice
            - status: "cloned" on success, "failed" on error
            - demo_audio_url: Optional URL to preview audio
        
    Audio Constraints (per official MiniMax API):
        - Duration: 10 seconds to 5 minutes
        - Formats: WAV, MP3, M4A
        - Max size: 20MB
        - Quality: Higher quality audio yields better voice clones
    
    Voice ID Details:
        - Format: [a-zA-Z][a-zA-Z0-9\\-_]{7,255}
        - Auto-generated if not specified
        - Cloned voices expire after 7 days
        - Voice synthesis within 168 hours makes voice permanent
    
    Note:
        Requires MINIMAX_API_KEY environment variable.
        Uses official MiniMax API: POST /voice_clone
    """
    logger.info(f"voice_clone called: voice_name={voice_name}, audio_bytes_len={len(audio_bytes)}")
    
    try:
        # Step 1: Validate input
        if not audio_bytes or len(audio_bytes) == 0:
            logger.error("Empty audio_bytes provided")
            return {
                "voice_id": "",
                "voice_name": voice_name,
                "status": "failed",
                "error": "Empty audio provided"
            }
        
        if not voice_name or len(voice_name.strip()) == 0:
            logger.error("Empty voice_name provided")
            return {
                "voice_id": "",
                "voice_name": voice_name,
                "status": "failed",
                "error": "Invalid voice name"
            }
        
        # Step 2: Upload audio file to MiniMax
        file_id = await upload_audio_file(
            audio_bytes=audio_bytes,
            filename=f"{voice_name.replace(' ', '_')}.wav",
            purpose="voice_clone"
        )
        
        if not file_id:
            logger.error("Failed to upload audio file")
            return {
                "voice_id": "",
                "voice_name": voice_name,
                "status": "failed",
                "error": "Audio upload failed"
            }
        
        # Step 3: Call voice clone API
        result = await call_voice_clone_api(
            file_id=file_id,
            voice_name=voice_name,
            voice_id=None,  # Auto-generate from voice_name
            apply_noise_reduction=True,
            apply_volume_normalization=True
        )
        
        if not result:
            logger.error("Voice clone API call failed")
            return {
                "voice_id": "",
                "voice_name": voice_name,
                "status": "failed",
                "error": "Voice cloning API failed"
            }
        
        return result
    
    except Exception as e:
        logger.error(f"voice_clone error: {e}", exc_info=True)
        return {
            "voice_id": "",
            "voice_name": voice_name,
            "status": "failed",
            "error": str(e)
        }



@mcp.tool()
async def text_to_audio(
    text: str,
    voice_id: str,
    language: str = "en",
) -> dict:
    """Generate audio from text using cloned voice.
    
    Args:
        text: Text to convert to speech
        voice_id: MiniMax voice_id to use for narration
        language: Language code (default: en)
    
    Returns:
        Dict with audio_url and duration_sec
        
    Note:
        Requires MINIMAX_API_KEY environment variable.
    """
    logger.info(f"text_to_audio called: text_len={len(text)}, voice_id={voice_id}")
    
    # TODO: Implement MiniMax API call
    # 1. Call MiniMax text_to_audio API
    # 2. Upload to S3/Azure
    # 3. Return audio_url and duration
    
    return {
        "audio_url": "s3://placeholder/audio.mp3",
        "duration_sec": 10.0,
        "status": "generated"
    }


@mcp.tool()
async def text_to_image(
    prompt: str,
    model: str = "minimax-image-v1",
    width: int = 1280,
    height: int = 720,
) -> dict:
    """Generate image from text prompt.
    
    Args:
        prompt: Text description of image to generate
        model: MiniMax image model to use
        width: Image width in pixels
        height: Image height in pixels
    
    Returns:
        Dict with image_url
        
    Note:
        Requires MINIMAX_API_KEY environment variable.
    """
    logger.info(f"text_to_image called: prompt_len={len(prompt)}, size={width}x{height}")
    
    # TODO: Implement MiniMax API call
    # 1. Call MiniMax text_to_image API
    # 2. Upload to S3/Azure
    # 3. Return image_url
    
    return {
        "image_url": "s3://placeholder/image.jpg",
        "width": width,
        "height": height,
        "status": "generated"
    }


@mcp.tool()
async def generate_video(
    prompt: str,
    first_frame_url: str,
    last_frame_url: str,
    duration_sec: int = 6,
    model: str = "minimax-video-v1",
) -> dict:
    """Generate video using first and last frame images.
    
    This is a wrapper that delegates to FL2V MCP server.
    
    Args:
        prompt: Video generation prompt
        first_frame_url: URL to first frame image
        last_frame_url: URL to last frame image
        duration_sec: Video duration (6 or 10)
        model: Video generation model
    
    Returns:
        Dict with task_id (poll for result)
    """
    logger.info(f"generate_video called: duration={duration_sec}s")
    
    # TODO: Forward to FL2V MCP server or call MiniMax API directly
    # 1. Call FL2V MCP: create_fl2v_task()
    # 2. Return task_id
    
    return {
        "task_id": "task_placeholder",
        "status": "submitted"
    }


@mcp.tool()
async def query_video_generation(task_id: str) -> dict:
    """Query status of video generation task.
    
    This tool polls MiniMax API to check the status of a video generation task.
    It follows the official polling pattern with exponential backoff for resilience.
    
    Args:
        task_id: Task ID returned from generate_video() call
    
    Returns:
        Dict with:
            - task_id: The queried task ID
            - status: One of "submitted", "processing", "completed", "failed", "unknown"
            - file_id: ID for file retrieval (present when status=="completed")
            - video_url: Placeholder for full video URL (None until implementation extends this)
            - error: Error message if status=="failed"
        
    Status Lifecycle:
        "submitted" → Task queued, waiting to start
        "processing" → Video generation in progress
        "completed" → Success, file_id provided for file retrieval
        "failed" → Generation failed, error message provided
    
    Polling Behavior (per official MiniMax API):
        - Recommended interval: 10 seconds between checks
        - Typical duration: 2-10 minutes depending on resolution
        - Rate limiting: Status polling doesn't count against video RPM limits
        - Exponential backoff: On transient errors (5xx), delays double
    
    Integration Flow:
        1. Call generate_video() → get task_id
        2. Poll with query_video_generation(task_id) every 10 seconds
        3. When status == "completed", file_id can be used to download video
        4. (Future) Implement file retrieval with file_id
    
    Note:
        Requires MINIMAX_API_KEY environment variable.
        Uses official MiniMax API: GET /v1/query/video_generation
    """
    logger.info(f"query_video_generation called: task_id={task_id}")
    
    try:
        # Validate input
        if not task_id or len(task_id.strip()) == 0:
            logger.error("Empty task_id provided")
            return {
                "task_id": task_id,
                "status": "failed",
                "error": "Invalid task_id"
            }
        
        # Query video generation status with retries
        result = await call_video_generation_status(
            task_id=task_id.strip(),
            max_retries=3,
            retry_delay=1.0
        )
        
        if not result:
            logger.error("Failed to query video generation status")
            return {
                "task_id": task_id,
                "status": "failed",
                "error": "Status query failed - please retry"
            }
        
        return result
    
    except Exception as e:
        logger.error(f"query_video_generation error: {e}", exc_info=True)
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e)
        }


def main():
    """Run the MCP server."""
    logger.info("Starting MiniMax MCP Server")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
