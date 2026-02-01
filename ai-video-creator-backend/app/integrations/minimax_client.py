"""MiniMax API client for video and audio generation."""

import asyncio
import base64
import logging
from typing import Optional, Dict, Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

MINIMAX_API_BASE = "https://api.minimax.io/v1"
TIMEOUT = httpx.Timeout(120.0, connect=30.0)


class MinimaxClient:
    """Client for MiniMax API operations."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.MINIMAX_API_KEY
        self.mock_mode = not self.api_key or self.api_key == ""
        
        if self.mock_mode:
            logger.warning("MiniMax API key not configured - running in MOCK mode")
        
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Make HTTP request to MiniMax API."""
        url = f"{MINIMAX_API_BASE}{endpoint}"

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.request(method, url, headers=self._headers, **kwargs)

            if response.status_code != 200:
                logger.error(f"MiniMax API error: {response.status_code} - {response.text}")
                raise Exception(f"MiniMax API error: {response.text}")

            data = response.json()

            # Check for API-level errors
            if data.get("base_resp", {}).get("status_code") != 0:
                error_msg = data.get("base_resp", {}).get("status_msg", "Unknown error")
                raise Exception(f"MiniMax API error: {error_msg}")

            return data

    # -------------------------------------------------------------------------
    # File Operations
    # -------------------------------------------------------------------------

    async def upload_file(
        self,
        file_bytes: bytes,
        filename: str,
        purpose: str = "voice_clone",
    ) -> str:
        """Upload file to MiniMax and return file_id.

        Args:
            file_bytes: File content as bytes
            filename: Original filename
            purpose: Purpose of upload (voice_clone, prompt_audio)

        Returns:
            file_id string
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Uploading file {filename} for {purpose}")
            return f"mock-file-{hash(filename) % 10000}"
        
        url = f"{MINIMAX_API_BASE}/files/upload"

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                files={"file": (filename, file_bytes)},
                data={"purpose": purpose},
            )

            data = response.json()

            if data.get("base_resp", {}).get("status_code") != 0:
                raise Exception(f"Upload failed: {data}")

            return data["file"]["file_id"]

    async def retrieve_file(self, file_id: str) -> str:
        """Get download URL for a file.

        Args:
            file_id: MiniMax file ID

        Returns:
            Download URL
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Retrieving file {file_id}")
            return f"https://mock-cdn.example.com/{file_id}.mp4"
        
        data = await self._request("GET", "/files/retrieve", params={"file_id": file_id})
        return data["file"]["download_url"]

    # -------------------------------------------------------------------------
    # Voice Operations
    # -------------------------------------------------------------------------

    async def voice_clone(
        self,
        file_id: str,
        voice_id: str,
        noise_reduction: bool = True,
        volume_normalization: bool = True,
    ) -> str:
        """Clone voice from uploaded audio file.

        Args:
            file_id: ID of uploaded audio file
            voice_id: Desired voice ID (alphanumeric)
            noise_reduction: Apply noise reduction
            volume_normalization: Apply volume normalization

        Returns:
            voice_id string (same as input if successful)
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Cloning voice with ID {voice_id} from file {file_id}")
            await asyncio.sleep(0.1)  # Simulate processing
            return voice_id
        
        await self._request(
            "POST",
            "/voice_clone",
            json={
                "file_id": file_id,
                "voice_id": voice_id,
                "need_noise_reduction": noise_reduction,
                "need_volume_normalization": volume_normalization,
            },
        )
        return voice_id

    async def text_to_audio(
        self,
        text: str,
        voice_id: str,
        model: str = "speech-02-hd",
        speed: float = 1.0,
        output_format: str = "mp3",
    ) -> bytes:
        """Generate audio from text using cloned voice.

        Args:
            text: Text to convert to speech
            voice_id: Cloned voice ID
            model: TTS model to use
            speed: Speech speed (0.5-2.0)
            output_format: Output format (mp3, wav, etc.)

        Returns:
            Audio bytes
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Generating audio for text (length: {len(text)}) with voice {voice_id}")
            # Return minimal valid MP3 header (silence)
            return b"\xff\xfb\x90\x00" + b"\x00" * 100
        
        url = f"{MINIMAX_API_BASE}/t2a_v2"

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                url,
                headers=self._headers,
                json={
                    "model": model,
                    "text": text,
                    "voice_setting": {
                        "voice_id": voice_id,
                        "speed": speed,
                    },
                    "audio_setting": {
                        "format": output_format,
                    },
                },
            )

            # For streaming audio, MiniMax returns binary directly
            # or JSON with base64 encoded audio
            content_type = response.headers.get("content-type", "")

            if "audio" in content_type:
                return response.content
            else:
                data = response.json()
                
                # Handle different response formats
                if "data" in data:
                    if isinstance(data["data"], dict) and "audio" in data["data"]:
                        # Base64 encoded audio
                        audio_b64 = data["data"]["audio"]
                        # Add padding if needed
                        missing_padding = len(audio_b64) % 4
                        if missing_padding:
                            audio_b64 += '=' * (4 - missing_padding)
                        return base64.b64decode(audio_b64)
                    elif isinstance(data["data"], str):
                        # Might be base64 string directly
                        audio_b64 = data["data"]
                        missing_padding = len(audio_b64) % 4
                        if missing_padding:
                            audio_b64 += '=' * (4 - missing_padding)
                        return base64.b64decode(audio_b64)
                
                # If we get here, the format is unexpected
                raise Exception(f"Unexpected TTS response format: {data}")

    # -------------------------------------------------------------------------
    # Video Operations - First & Last Frame Video Generation (FL2V)
    # -------------------------------------------------------------------------

    async def generate_video_fl2v(
        self,
        prompt: str,
        last_frame_image: str,
        first_frame_image: Optional[str] = None,
        model: str = "MiniMax-Hailuo-02",
        duration: int = 6,
        resolution: str = "768P",
        prompt_optimizer: bool = True,
        callback_url: Optional[str] = None,
    ) -> str:
        """Start First & Last Frame video generation task (FL2V).

        Args:
            prompt: Video generation prompt (max 2000 chars).
                   Can include camera commands like [Zoom in], [Pan left], etc.
            last_frame_image: Required. URL or base64 data URL of last frame
                             Format: URL or "data:image/jpeg;base64,..."
            first_frame_image: Optional. URL or base64 data URL of first frame
            model: Video model - must be "MiniMax-Hailuo-02" for FL2V
            duration: Video duration in seconds (6 or 10 for FL2V)
            resolution: Video resolution (768P or 1080P - 512P NOT supported for FL2V)
            prompt_optimizer: Auto-optimize prompt (default True, set False for precise control)
            callback_url: Optional webhook URL for async status updates

        Returns:
            task_id for polling
        """
        payload: Dict[str, Any] = {
            "model": model,
            "last_frame_image": last_frame_image,
            "duration": duration,
            "resolution": resolution,
            "prompt_optimizer": prompt_optimizer,
        }

        if prompt:
            payload["prompt"] = prompt[:2000]

        if first_frame_image:
            payload["first_frame_image"] = first_frame_image

        if callback_url:
            payload["callback_url"] = callback_url

        data = await self._request("POST", "/video_generation", json=payload)
        return data["task_id"]

    async def generate_video(
        self,
        prompt: str,
        first_frame_image: str,
        last_frame_image: Optional[str] = None,
        model: str = "MiniMax-Hailuo-02",
        duration: int = 6,
        resolution: str = "720P",
    ) -> str:
        """Start video generation task.

        Args:
            prompt: Video generation prompt
            first_frame_image: URL or base64 of first frame
            last_frame_image: URL or base64 of last frame (optional)
            model: Video model to use
            duration: Video duration in seconds (6 or 10)
            resolution: Video resolution

        Returns:
            task_id for polling
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Generating video: {prompt[:50]}...")
            return f"mock-task-{hash(prompt) % 10000}"
        
        payload: Dict[str, Any] = {
            "prompt": prompt,
            "first_frame_image": first_frame_image,
            "model": model,
            "duration": duration,
            "resolution": resolution,
        }

        if last_frame_image:
            payload["last_frame_image"] = last_frame_image

        data = await self._request("POST", "/video_generation", json=payload)
        return data["task_id"]

    async def query_video_status(self, task_id: str) -> Dict[str, Any]:
        """Query video generation status.

        Args:
            task_id: Task ID from generate_video

        Returns:
            Dict with status, file_id (if complete), error (if failed)
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Querying status for task {task_id}")
            # Always return success for mock mode
            return {
                "task_id": task_id,
                "status": "Success",
                "file_id": f"mock-file-{task_id}",
            }
        
        data = await self._request(
            "GET",
            "/query/video_generation",
            params={"task_id": task_id},
        )

        return {
            "task_id": task_id,
            "status": data.get("status", "unknown"),
            "file_id": data.get("file_id"),
        }

    async def poll_video_until_complete(
        self,
        task_id: str,
        interval: float = 10.0,
        max_attempts: int = 60,
    ) -> Dict[str, Any]:
        """Poll video generation until complete or failed.

        Args:
            task_id: Task ID to poll
            interval: Seconds between polls (recommended: 10)
            max_attempts: Maximum polling attempts

        Returns:
            Final status with file_id or error
        """
        for attempt in range(max_attempts):
            status = await self.query_video_status(task_id)

            if status["status"] == "Success":
                # Get download URL
                download_url = await self.retrieve_file(status["file_id"])
                status["download_url"] = download_url
                return status

            elif status["status"] == "Fail":
                raise Exception(f"Video generation failed: {status}")

            # Still processing
            logger.info(f"Video generation in progress... attempt {attempt + 1}")
            await asyncio.sleep(interval)

        raise Exception(f"Video generation timed out after {max_attempts} attempts")


# Global client instance
minimax_client = MinimaxClient()

# Backwards-compatible alias for tests/legacy code
MiniMaxClient = MinimaxClient
