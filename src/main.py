"""Main entry point for video creator application."""

import asyncio
import logging
from pathlib import Path

from src.config import Settings
from src.core.orchestrator import VideoOrchestrator

# Configure logging to stderr (never stdout for MCP servers)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def create_sample_video():
    """Create a sample video demonstrating the full pipeline."""
    logger.info("=== Video Creator Application ===")
    
    settings = Settings()
    orchestrator = VideoOrchestrator(settings)
    
    # Step 1: Create video plan
    logger.info("\n[STEP 1] Creating video plan...")
    plan = await orchestrator.create_video_plan(
        project_id="demo_project_001",
        story_prompt="A beautiful journey through nature",
        target_duration_sec=12,
        segment_len_sec=6,
    )
    logger.info(f"✓ Video plan created: {plan.segment_count} segments")
    
    # Step 2: Clone voice
    logger.info("\n[STEP 2] Cloning voice...")
    # Create a minimal audio bytes for demo (would normally be from file)
    demo_audio = b"RIFF" + b"\x00" * 100  # Minimal WAV header
    voice_id = await orchestrator.clone_voice(
        voice_sample_bytes=demo_audio,
        voice_name="narrator",
    )
    if voice_id:
        plan.voice_id = voice_id
        logger.info(f"✓ Voice cloned: {voice_id}")
    else:
        logger.error("✗ Voice cloning failed")
        return
    
    # Step 3: Process segments
    logger.info("\n[STEP 3] Processing segments...")
    for segment in plan.segments:
        # Update with sample data
        segment.prompt = f"A scenic view showing nature segment {segment.segment_index}"
        segment.narration_text = f"Narrator: This is segment {segment.segment_index} of our nature journey"
        
        success = await orchestrator.process_segment(
            segment=segment,
            voice_id=voice_id,
        )
        if success:
            logger.info(f"✓ Segment {segment.segment_index} processed")
        else:
            logger.error(f"✗ Segment {segment.segment_index} failed")
    
    # Step 4: Finalize video
    logger.info("\n[STEP 4] Finalizing video...")
    final_url = await orchestrator.finalize_video(plan)
    
    if final_url:
        logger.info(f"✓ Video finalized: {final_url}")
    else:
        logger.info("✓ Video finalization initiated (check logs for details)")
    
    logger.info("\n=== Pipeline Complete ===")
    return plan


async def main():
    """Main application entry point."""
    logger.info("Starting Video Creator Application")
    
    try:
        plan = await create_sample_video()
        if plan:
            logger.info(f"\nProject {plan.project_id} ready for deployment")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
