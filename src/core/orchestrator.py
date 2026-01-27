"""Orchestrator for video creation workflow."""

import asyncio
import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import httpx

from src.config import Settings
from src.models.video_plan import VideoPlan
from src.models.segment import SegmentStatus
from src.ai.prompt_generator import (
    generate_story_plan,
    generate_story_plan_fallback,
    create_default_prompts,
)

logger = logging.getLogger(__name__)

# MiniMax API Configuration
MINIMAX_API_BASE = "https://api.minimaxi.com/v1"
MINIMAX_TIMEOUT = 120.0  # 2 minutes for async operations


class VideoOrchestrator:
    """Main orchestrator for the video creation process.
    
    Responsibilities:
    1. Create VideoPlan from user inputs (story, voice, duration, segment_len)
    2. Clone voice → get voice_id
    3. Loop through segments:
       - Extract first_frame (from previous segment or initial frame)
       - Generate end_frame_image
       - Call FL2V MCP → generate segment video
       - Call MiniMax MCP → generate segment audio
       - Present to HITL gate for approval
    4. Finalize: concat videos + audios → mux → final_video
    """
    
    def __init__(self, settings: Settings):
        """Initialize orchestrator.
        
        Args:
            settings: Application configuration
        """
        self.settings = settings
        self._ensure_directories()
        self._openai_client = None
        logger.info("VideoOrchestrator initialized")
    
    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        self.settings.project_root_path.mkdir(parents=True, exist_ok=True)
        self.settings.temp_folder.mkdir(parents=True, exist_ok=True)
    
    def _get_openai_client(self):
        """Get or create OpenAI client (lazy initialization).
        
        Returns:
            AsyncOpenAI client or None if not configured
        """
        if self._openai_client is not None:
            return self._openai_client
        
        if not self.settings.openai_api_key:
            logger.warning("OPENAI_API_KEY not configured")
            return None
        
        try:
            from openai import AsyncOpenAI
            self._openai_client = AsyncOpenAI(api_key=self.settings.openai_api_key)
            logger.info("OpenAI client initialized")
            return self._openai_client
        except ImportError:
            logger.error("openai package not installed")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            return None
    
    async def create_video_plan(
        self,
        project_id: str,
        story_prompt: str,
        target_duration_sec: int,
        segment_len_sec: int,
        use_ai: bool = True,
    ) -> VideoPlan:
        """Create a video plan from user inputs with AI-generated prompts.
        
        Args:
            project_id: Unique project identifier
            story_prompt: User's story/concept for the video
            target_duration_sec: Target video duration (max 60)
            segment_len_sec: Length of each segment (6 or 10)
            use_ai: Whether to use AI for prompt generation (default: True)
        
        Returns:
            VideoPlan object with AI-generated segment prompts
            
        Note:
            Uses OpenAI's structured outputs feature for reliable prompt generation.
            Falls back to placeholder prompts if AI is unavailable or disabled.
        """
        logger.info(f"Creating video plan for project {project_id}")
        
        # Validate inputs
        assert target_duration_sec <= 60, "Target duration must be ≤ 60 seconds"
        assert segment_len_sec in (6, 10), "Segment length must be 6 or 10 seconds"
        
        segment_count = target_duration_sec // segment_len_sec
        
        # Initialize base plan
        video_plan = VideoPlan(
            project_id=project_id,
            target_duration_sec=target_duration_sec,
            segment_len_sec=segment_len_sec,
            segment_count=segment_count,
        )
        
        # Generate intelligent prompts using AI
        if use_ai:
            openai_client = self._get_openai_client()
            
            if openai_client:
                try:
                    logger.info("Generating AI-powered segment prompts...")
                    
                    # Use structured outputs for reliable JSON
                    story_plan = await generate_story_plan(
                        story_prompt=story_prompt,
                        segment_count=segment_count,
                        segment_len_sec=segment_len_sec,
                        openai_client=openai_client,
                    )
                    
                    logger.info(f"✓ AI generation complete: {story_plan.title}")
                    logger.debug(f"Continuity: {story_plan.continuity_notes}")
                    
                    # Convert AI-generated segments to SegmentStatus objects
                    for ai_segment in story_plan.segments:
                        segment = SegmentStatus(
                            segment_index=ai_segment.segment_index,
                            prompt=ai_segment.video_prompt,
                            narration_text=ai_segment.narration_text,
                        )
                        # Store end_frame_prompt as last_frame_image_url placeholder
                        # (will be replaced with actual URL during generation)
                        video_plan.segments.append(segment)
                    
                except Exception as e:
                    logger.error(f"AI prompt generation failed: {e}")
                    logger.info("Falling back to default prompts")
                    story_plan = create_default_prompts(story_prompt, segment_count)
                    
                    for ai_segment in story_plan.segments:
                        segment = SegmentStatus(
                            segment_index=ai_segment.segment_index,
                            prompt=ai_segment.video_prompt,
                            narration_text=ai_segment.narration_text,
                        )
                        video_plan.segments.append(segment)
            else:
                logger.warning("OpenAI client unavailable - using default prompts")
                story_plan = create_default_prompts(story_prompt, segment_count)
                
                for ai_segment in story_plan.segments:
                    segment = SegmentStatus(
                        segment_index=ai_segment.segment_index,
                        prompt=ai_segment.video_prompt,
                        narration_text=ai_segment.narration_text,
                    )
                    video_plan.segments.append(segment)
        else:
            # Manual mode: create placeholder prompts
            logger.info("AI disabled - creating placeholder prompts")
            for i in range(segment_count):
                segment = SegmentStatus(
                    segment_index=i,
                    prompt=f"[Segment {i} video prompt - Please edit manually]",
                    narration_text=f"[Segment {i} narration - Please edit manually]",
                )
                video_plan.segments.append(segment)
        
        logger.info(f"Video plan created: {segment_count} segments")
        return video_plan
    
    async def clone_voice(
        self,
        voice_sample_bytes: bytes,
        voice_name: str,
    ) -> Optional[str]:
        """Clone voice from audio sample and return voice_id.
        
        Args:
            voice_sample_bytes: Audio bytes of voice sample (WAV, MP3, or M4A)
            voice_name: Name for the cloned voice
        
        Returns:
            MiniMax voice_id or None if failed
            
        Note:
            Requires MINIMAX_API_KEY in environment.
            Audio constraints: 10 seconds to 5 minutes, max 20MB.
            Uses MiniMax API directly for voice cloning.
        """
        logger.info(f"Cloning voice: {voice_name} ({len(voice_sample_bytes)} bytes)")
        
        # Validate audio size
        max_size_mb = 20
        size_mb = len(voice_sample_bytes) / (1024 * 1024)
        if size_mb > max_size_mb:
            logger.error(f"Audio sample too large: {size_mb:.2f}MB > {max_size_mb}MB")
            return None
        
        # Get API key from settings
        api_key = self.settings.minimax_api_key
        if not api_key:
            logger.error("MINIMAX_API_KEY not configured in settings")
            return None
        
        try:
            # Step 1: Upload audio file to MiniMax
            logger.info("Uploading audio file to MiniMax...")
            file_id = await self._upload_audio_file(
                audio_bytes=voice_sample_bytes,
                filename=f"{voice_name.replace(' ', '_')}.wav",
                api_key=api_key,
            )
            
            if not file_id:
                logger.error("Failed to upload audio file")
                return None
            
            logger.info(f"Audio uploaded successfully. file_id={file_id}")
            
            # Step 2: Call voice clone API
            logger.info("Calling voice clone API...")
            voice_id = await self._call_voice_clone_api(
                file_id=file_id,
                voice_name=voice_name,
                api_key=api_key,
            )
            
            if not voice_id:
                logger.error("Voice clone API call failed")
                return None
            
            logger.info(f"✓ Voice cloned successfully: {voice_id}")
            return voice_id
        
        except Exception as e:
            logger.error(f"Voice cloning failed: {e}", exc_info=True)
            return None
    
    async def _upload_audio_file(
        self,
        audio_bytes: bytes,
        filename: str,
        api_key: str,
    ) -> Optional[str]:
        """Upload audio file to MiniMax and return file_id.
        
        Args:
            audio_bytes: Audio file bytes
            filename: Original filename (e.g., "sample.wav")
            api_key: MiniMax API key
        
        Returns:
            file_id string on success, None on failure
        """
        try:
            # Prepare multipart form data
            files = {
                "file": (filename, io.BytesIO(audio_bytes), "audio/wav"),
                "purpose": (None, "voice_clone"),
            }
            
            headers = {
                "Authorization": f"Bearer {api_key}"
            }
            
            # Upload file
            async with httpx.AsyncClient(timeout=MINIMAX_TIMEOUT) as client:
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
                
                return file_id
        
        except Exception as e:
            logger.error(f"Upload error: {e}", exc_info=True)
            return None
    
    async def _call_voice_clone_api(
        self,
        file_id: str,
        voice_name: str,
        api_key: str,
    ) -> Optional[str]:
        """Call MiniMax voice clone API.
        
        Args:
            file_id: ID of uploaded audio file
            voice_name: Friendly name for the cloned voice
            api_key: MiniMax API key
        
        Returns:
            voice_id string on success, None on failure
        """
        try:
            # Generate voice_id from voice_name
            base = voice_name.replace(" ", "_").replace("-", "_")
            if not base or not base[0].isalpha():
                base = "voice_" + base
            voice_id = base[:256]  # Ensure reasonable length
            
            # Prepare request payload
            payload = {
                "file_id": file_id,
                "voice_id": voice_id,
                "need_noise_reduction": True,
                "need_volume_normalization": True,
            }
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Call voice clone API
            async with httpx.AsyncClient(timeout=MINIMAX_TIMEOUT) as client:
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
                
                return voice_id
        
        except Exception as e:
            logger.error(f"Voice clone API error: {e}", exc_info=True)
            return None
    
    async def extract_audio_from_video(
        self,
        video_path: Path,
        output_audio_path: Optional[Path] = None,
    ) -> Optional[Path]:
        """Extract audio track from video file.
        
        Args:
            video_path: Path to video file
            output_audio_path: Optional output path (auto-generated if not provided)
        
        Returns:
            Path to extracted audio file, or None if failed
            
        Note:
            Uses FFmpeg to extract audio without re-encoding.
            Outputs to WAV format for compatibility with voice cloning.
        """
        logger.info(f"Extracting audio from video: {video_path}")
        
        if not video_path.exists():
            logger.error(f"Video file not found: {video_path}")
            return None
        
        try:
            # Auto-generate output path if not provided
            if output_audio_path is None:
                output_audio_path = self.settings.temp_folder / f"{video_path.stem}_audio.wav"
            
            # Use FFmpeg to extract audio
            cmd = [
                "ffmpeg",
                "-i", str(video_path),
                "-vn",  # No video
                "-acodec", "pcm_s16le",  # WAV format
                "-ar", "44100",  # 44.1kHz sample rate
                "-ac", "2",  # Stereo
                "-y",  # Overwrite output
                str(output_audio_path)
            ]
            
            logger.debug(f"Running: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"✓ Audio extracted: {output_audio_path}")
                return output_audio_path
            else:
                logger.error(f"FFmpeg failed: {stderr.decode()}")
                return None
        
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}", exc_info=True)
            return None
    
    async def clone_voice_from_video(
        self,
        video_path: Path,
        voice_name: str,
    ) -> Optional[str]:
        """Extract audio from video and clone voice.
        
        Args:
            video_path: Path to video file containing voice sample
            voice_name: Name for the cloned voice
        
        Returns:
            MiniMax voice_id or None if failed
            
        Note:
            This is a convenience method that combines:
            1. Audio extraction from video
            2. Voice cloning from audio bytes
        """
        logger.info(f"Cloning voice from video: {video_path}")
        
        # Extract audio
        audio_path = await self.extract_audio_from_video(video_path)
        if not audio_path:
            return None
        
        try:
            # Read audio bytes
            with open(audio_path, 'rb') as f:
                audio_bytes = f.read()
            
            # Clone voice
            voice_id = await self.clone_voice(audio_bytes, voice_name)
            
            # Cleanup temp audio file
            try:
                audio_path.unlink()
                logger.debug(f"Cleaned up temp audio: {audio_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp audio: {e}")
            
            return voice_id
        
        except Exception as e:
            logger.error(f"Failed to read audio file: {e}")
            return None
    
    async def process_segment(
        self,
        segment: SegmentStatus,
        voice_id: str,
        first_frame_path: Optional[str] = None,
        max_retries: int = 3,
    ) -> bool:
        """Process a single segment through generation and HITL gate.
        
        Args:
            segment: Segment to process
            voice_id: Voice ID for audio generation
            first_frame_path: Path to first frame image (optional)
            max_retries: Maximum number of retry attempts
        
        Returns:
            True if approved, False otherwise
            
        Note:
            This method encapsulates the per-segment workflow:
            1. Generate end-frame image
            2. Call FL2V MCP to generate video
            3. Call MiniMax MCP to generate audio
            4. Present to HITL gate
            5. Loop if regeneration requested
        """
        logger.info(f"Processing segment {segment.segment_index}")
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Segment {segment.segment_index} - Attempt {attempt + 1}/{max_retries}")
                
                # Update timestamp
                segment.updated_at = datetime.utcnow()
                
                # TODO: Implement actual generation workflow when MCP tools are integrated
                # 1. Generate last_frame_image using text_to_image
                # 2. Create FL2V task with first+last frames
                # 3. Generate audio using text_to_audio
                # 4. Wait for HITL approval
                
                logger.info(f"Segment {segment.segment_index} processing complete")
                segment.approved = True
                segment.approval_timestamp = datetime.utcnow()
                return True
            
            except Exception as e:
                logger.error(f"Segment {segment.segment_index} attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Segment {segment.segment_index} failed after {max_retries} attempts")
                    return False
        
        return False
    
    async def finalize_video(self, video_plan: VideoPlan) -> Optional[str]:
        """Finalize video by concatenating and muxing.
        
        Args:
            video_plan: Completed video plan with all approved segments
        
        Returns:
            URL to final muxed video, or None if failed
            
        Raises:
            ValueError: If not all segments are approved
        """
        logger.info(f"Finalizing video for project {video_plan.project_id}")
        
        # Validate all segments are approved
        unapproved = [s.segment_index for s in video_plan.segments if not s.approved]
        if unapproved:
            raise ValueError(f"Cannot finalize: segments {unapproved} not approved")
        
        try:
            # TODO: Implement finalization:
            # 1. Collect all segment_video_urls
            video_urls = [s.segment_video_url for s in video_plan.segments if s.segment_video_url]
            logger.debug(f"Collected {len(video_urls)} video segments")
            
            # 2. Call MediaOps MCP: concat_videos()
            # assembled_video_url = await concat_videos(video_urls)
            
            # 3. Collect all segment_audio_urls
            audio_urls = [s.segment_audio_url for s in video_plan.segments if s.segment_audio_url]
            logger.debug(f"Collected {len(audio_urls)} audio segments")
            
            # 4. Call MediaOps MCP: concat_audios()
            # assembled_audio_url = await concat_audios(audio_urls)
            
            # 5. Call MediaOps MCP: mux_audio_video()
            # final_video_url = await mux_audio_video(assembled_video_url, assembled_audio_url)
            
            # 6. Update plan
            video_plan.updated_at = datetime.utcnow()
            
            logger.info("Video finalization complete")
            return None
        
        except Exception as e:
            logger.error(f"Video finalization failed: {e}", exc_info=True)
            return None
    
    def validate_plan(self, video_plan: VideoPlan) -> Dict[str, Any]:
        """Validate video plan integrity.
        
        Args:
            video_plan: Video plan to validate
            
        Returns:
            Dictionary with validation results
        """
        issues = []
        warnings = []
        
        # Check duration constraint
        if video_plan.target_duration_sec > 60:
            issues.append(f"Target duration {video_plan.target_duration_sec}s exceeds 60s limit")
        
        # Check segment length
        if video_plan.segment_len_sec not in (6, 10):
            issues.append(f"Segment length {video_plan.segment_len_sec}s must be 6 or 10")
        
        # Check segment count matches
        expected_count = video_plan.target_duration_sec // video_plan.segment_len_sec
        if video_plan.segment_count != expected_count:
            issues.append(f"Segment count {video_plan.segment_count} doesn't match expected {expected_count}")
        
        # Check all segments are present
        if len(video_plan.segments) != video_plan.segment_count:
            issues.append(f"Expected {video_plan.segment_count} segments, found {len(video_plan.segments)}")
        
        # Check for duplicate indices
        indices = [s.segment_index for s in video_plan.segments]
        if len(indices) != len(set(indices)):
            issues.append("Duplicate segment indices found")
        
        # Warnings for incomplete segments
        for segment in video_plan.segments:
            if not segment.prompt or segment.prompt.startswith("[Segment"):
                warnings.append(f"Segment {segment.segment_index} has placeholder prompt")
            if not segment.narration_text or segment.narration_text.startswith("[Segment"):
                warnings.append(f"Segment {segment.segment_index} has placeholder narration")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'segment_count': len(video_plan.segments),
            'approved_count': sum(1 for s in video_plan.segments if s.approved)
        }
    
    async def save_plan(self, video_plan: VideoPlan, path: Optional[Path] = None) -> Path:
        """Save video plan to disk.
        
        Args:
            video_plan: Video plan to save
            path: Optional custom path (defaults to project folder)
            
        Returns:
            Path where plan was saved
        """
        if path is None:
            project_dir = self.settings.project_root_path / video_plan.project_id
            project_dir.mkdir(parents=True, exist_ok=True)
            path = project_dir / "video_plan.json"
        
        with open(path, 'w') as f:
            f.write(video_plan.model_dump_json(indent=2))
        
        logger.info(f"Video plan saved to {path}")
        return path
    
    async def load_plan(self, path: Path) -> VideoPlan:
        """Load video plan from disk.
        
        Args:
            path: Path to saved plan
            
        Returns:
            Loaded video plan
        """
        with open(path, 'r') as f:
            data = f.read()
        
        plan = VideoPlan.model_validate_json(data)
        logger.info(f"Video plan loaded from {path}")
        return plan
