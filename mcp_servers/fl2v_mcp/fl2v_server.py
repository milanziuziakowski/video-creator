"""FL2V MCP Server - First-Last Frame Video Generation.

This server handles video generation with first and last frame control:
- create_fl2v_task: Submit video generation task with frame constraints
- query_task_status: Poll video generation status

The FL2V (First-Last Frame Video) model generates videos that start and end
with specific frames, enabling seamless segment transitions.
"""

import asyncio
import base64
import io
import logging
import os
from pathlib import Path
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

# Configure logging to stderr (never stdout for MCP)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configuration
FL2V_API_KEY = os.getenv("MINIMAX_API_KEY")  # FL2V uses MiniMax API key
FL2V_API_BASE = "https://api.minimaxi.com"
FL2V_TIMEOUT = 120  # 2 minutes for video generation calls

# Initialize FastMCP server
mcp = FastMCP("fl2v")


async def _image_to_base64(image_path: str) -> Optional[str]:
    """Convert image file to Base64 data URL.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Base64 data URL or None on error
    """
    try:
        path = Path(image_path)
        if not path.exists():
            logger.error(f"Image file not found: {image_path}")
            return None
        
        with open(path, "rb") as f:
            image_data = f.read()
        
        # Determine MIME type
        suffix = path.suffix.lower()
        mime_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }.get(suffix, "image/jpeg")
        
        b64 = base64.b64encode(image_data).decode("utf-8")
        return f"data:{mime_type};base64,{b64}"
    
    except Exception as e:
        logger.error(f"Error converting image to base64: {e}")
        return None


async def _call_fl2v_api(
    prompt: str,
    first_frame_url: str,
    last_frame_url: str,
    duration_sec: int = 6,
    resolution: str = "768P",
) -> Optional[dict]:
    """Call MiniMax FL2V API to generate video.
    
    Args:
        prompt: Video generation prompt
        first_frame_url: Base64 or HTTP URL for first frame
        last_frame_url: Base64 or HTTP URL for last frame
        duration_sec: Duration in seconds (6 or 10)
        resolution: Resolution (512P, 768P, or 1080P)
        
    Returns:
        Dict with task_id or None on error
    """
    if not FL2V_API_KEY:
        logger.error("FL2V_API_KEY not set in environment")
        return None
    
    headers = {
        "Authorization": f"Bearer {FL2V_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "MiniMax-Hailuo-02",
        "prompt": prompt,
        "first_frame_image": first_frame_url,
        "last_frame_image": last_frame_url,
        "duration_sec": duration_sec,
        "resolution": resolution,
    }
    
    try:
        async with httpx.AsyncClient(timeout=FL2V_TIMEOUT) as client:
            response = await client.post(
                f"{FL2V_API_BASE}/v1/video_generation",
                json=payload,
                headers=headers,
            )
            
            if response.status_code == 200:
                data = response.json()
                base_resp = data.get("base_resp", {})
                
                if base_resp.get("status_code") == 0:
                    task_id = data.get("task_id")
                    logger.info(f"FL2V task created: {task_id}")
                    return {
                        "task_id": task_id,
                        "status": "submitted",
                    }
                else:
                    error_msg = base_resp.get("status_msg", "Unknown API error")
                    logger.error(f"FL2V API error: {error_msg}")
                    return {"error": error_msg}
            
            elif response.status_code == 429:
                logger.warning("FL2V rate limited (429)")
                return {"error": "Rate limited, retry after 60s"}
            
            else:
                logger.error(f"FL2V API error: {response.status_code} {response.text}")
                return {"error": f"HTTP {response.status_code}"}
    
    except asyncio.TimeoutError:
        logger.error("FL2V API timeout")
        return {"error": "API timeout"}
    except Exception as e:
        logger.error(f"Error calling FL2V API: {e}")
        return {"error": str(e)}


async def _poll_fl2v_status(
    task_id: str,
    max_retries: int = 60,
    retry_delay: float = 10,
) -> Optional[dict]:
    """Poll FL2V task status with exponential backoff.
    
    Args:
        task_id: Task ID from create_fl2v_task
        max_retries: Maximum number of retries
        retry_delay: Initial delay between retries (exponential)
        
    Returns:
        Dict with status and file_id or None
    """
    if not FL2V_API_KEY:
        logger.error("FL2V_API_KEY not set in environment")
        return None
    
    headers = {
        "Authorization": f"Bearer {FL2V_API_KEY}",
    }
    
    current_delay = retry_delay
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            async with httpx.AsyncClient(timeout=FL2V_TIMEOUT) as client:
                response = await client.get(
                    f"{FL2V_API_BASE}/v1/query/video_generation",
                    params={"task_id": task_id},
                    headers=headers,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    base_resp = data.get("base_resp", {})
                    
                    if base_resp.get("status_code") != 0:
                        error_msg = base_resp.get("status_msg", "Unknown error")
                        logger.error(f"FL2V status error: {error_msg}")
                        return {"status": "failed", "error": error_msg}
                    
                    status = data.get("status")
                    
                    # Normalize status values
                    if status == "Success":
                        file_id = data.get("file_id")
                        logger.info(f"FL2V task completed: {task_id} -> {file_id}")
                        return {
                            "task_id": task_id,
                            "status": "completed",
                            "file_id": file_id,
                        }
                    
                    elif status == "Fail":
                        logger.error(f"FL2V task failed: {task_id}")
                        return {
                            "task_id": task_id,
                            "status": "failed",
                            "error": "Video generation failed on server",
                        }
                    
                    else:  # submitted, processing
                        logger.debug(f"FL2V task {task_id} status: {status}")
                        await asyncio.sleep(current_delay)
                        current_delay = min(current_delay * 2, 30)  # Cap at 30s
                        retry_count += 1
                
                elif response.status_code == 429:
                    logger.warning(f"FL2V rate limited, retrying in {current_delay}s")
                    await asyncio.sleep(current_delay)
                    current_delay = min(current_delay * 2, 30)
                    retry_count += 1
                
                else:
                    logger.error(f"FL2V status API error: {response.status_code}")
                    await asyncio.sleep(current_delay)
                    current_delay = min(current_delay * 2, 30)
                    retry_count += 1
        
        except asyncio.TimeoutError:
            logger.warning("FL2V poll timeout, retrying...")
            await asyncio.sleep(current_delay)
            current_delay = min(current_delay * 2, 30)
            retry_count += 1
        except Exception as e:
            logger.error(f"Error polling FL2V status: {e}")
            await asyncio.sleep(current_delay)
            current_delay = min(current_delay * 2, 30)
            retry_count += 1
    
    logger.error(f"FL2V polling timeout after {max_retries} retries")
    return {"status": "timeout", "error": "Polling timeout"}


@mcp.tool()
async def create_fl2v_task(
    prompt: str,
    first_frame_image_path: str,
    last_frame_image_path: str,
    duration_sec: int = 6,
    model: str = "minimax-fl2v-v1",
    resolution: str = "1280x720",
) -> dict:
    """Create a first-last frame video generation task.
    
    Args:
        prompt: Video generation prompt describing the scene
        first_frame_image_path: Path to first frame image (constraints video start)
        last_frame_image_path: Path to last frame image (constraints video end)
        duration_sec: Video duration in seconds (6 or 10)
        model: FL2V model to use
        resolution: Video resolution (default: 1280x720)
    
    Returns:
        Dict with task_id (use for polling status) or error
        
    Note:
        Requires MINIMAX_API_KEY environment variable.
        Use query_task_status() to poll for completion.
    """
    logger.info(
        f"create_fl2v_task: prompt_len={len(prompt)}, "
        f"duration={duration_sec}s, resolution={resolution}"
    )
    
    # Validate inputs
    if not prompt or len(prompt.strip()) == 0:
        return {"error": "prompt cannot be empty"}
    
    if not first_frame_image_path or not last_frame_image_path:
        return {"error": "first_frame_image_path and last_frame_image_path required"}
    
    if duration_sec not in (6, 10):
        return {"error": "duration_sec must be 6 or 10"}
    
    # Convert images to Base64
    first_frame_url = await _image_to_base64(first_frame_image_path)
    if not first_frame_url:
        return {"error": f"Cannot load first frame: {first_frame_image_path}"}
    
    last_frame_url = await _image_to_base64(last_frame_image_path)
    if not last_frame_url:
        return {"error": f"Cannot load last frame: {last_frame_image_path}"}
    
    # Map resolution
    resolution_map = {
        "512x288": "512P",
        "768x432": "768P",
        "1280x720": "768P",
        "1920x1080": "1080P",
    }
    fl2v_resolution = resolution_map.get(resolution, "768P")
    
    # Call FL2V API
    result = await _call_fl2v_api(
        prompt=prompt,
        first_frame_url=first_frame_url,
        last_frame_url=last_frame_url,
        duration_sec=duration_sec,
        resolution=fl2v_resolution,
    )
    
    if result and "error" not in result:
        return {
            "task_id": result.get("task_id"),
            "status": "submitted",
            "estimated_wait_sec": 30,
        }
    
    return result or {"error": "Unknown error"}


@mcp.tool()
async def query_task_status(task_id: str) -> dict:
    """Poll status of video generation task.
    
    Args:
        task_id: Task ID from create_fl2v_task() call
    
    Returns:
        Dict with status and video_url (if ready)
        
    Note:
        Status can be: submitted, processing, completed, failed
        Video generation typically takes 20-60 seconds.
    """
    logger.info(f"query_task_status: task_id={task_id}")
    
    if not task_id or len(task_id.strip()) == 0:
        return {"error": "task_id cannot be empty"}
    
    # Poll until completion or timeout
    result = await _poll_fl2v_status(task_id)
    
    if result:
        return result
    
    return {"task_id": task_id, "status": "error", "error": "Polling failed"}


def main():
    """Run the MCP server."""
    logger.info("Starting FL2V MCP Server")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
