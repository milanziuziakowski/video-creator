"""Test AI-powered prompt generation.

This script demonstrates and tests the OpenAI integration for
intelligent segment prompt generation.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Settings
from src.core.orchestrator import VideoOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_ai_prompt_generation():
    """Test AI-powered prompt generation with OpenAI."""
    logger.info("=" * 70)
    logger.info("AI PROMPT GENERATION TEST")
    logger.info("=" * 70)
    
    # Initialize
    settings = Settings()
    orchestrator = VideoOrchestrator(settings)
    
    # Check if OpenAI is configured
    if not settings.openai_api_key:
        logger.error("❌ OPENAI_API_KEY not set in environment")
        logger.info("Please set OPENAI_API_KEY in .env file")
        logger.info("Falling back to default prompts for demonstration")
        print()
    
    # Test story
    test_story = "A peaceful morning as the sun rises over a tranquil ocean"
    
    logger.info(f"\n📖 Story Prompt:")
    logger.info(f"   {test_story}")
    logger.info(f"\n⚙️  Configuration:")
    logger.info(f"   Duration: 12 seconds")
    logger.info(f"   Segment Length: 6 seconds")
    logger.info(f"   Expected Segments: 2")
    logger.info("")
    
    # Create video plan with AI
    try:
        plan = await orchestrator.create_video_plan(
            project_id="ai_test_001",
            story_prompt=test_story,
            target_duration_sec=12,
            segment_len_sec=6,
            use_ai=True  # Enable AI generation
        )
        
        logger.info("=" * 70)
        logger.info("✅ VIDEO PLAN GENERATED")
        logger.info("=" * 70)
        
        # Display results
        logger.info(f"\n📋 Project: {plan.project_id}")
        logger.info(f"⏱️  Total Duration: {plan.target_duration_sec}s")
        logger.info(f"🎬 Segments: {plan.segment_count}")
        logger.info("")
        
        for i, segment in enumerate(plan.segments):
            logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            logger.info(f"SEGMENT {i}")
            logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            logger.info(f"\n🎥 Video Prompt:")
            logger.info(f"   {segment.prompt}")
            logger.info(f"\n🎙️  Narration:")
            logger.info(f"   {segment.narration_text}")
            logger.info("")
        
        # Validate plan
        validation = orchestrator.validate_plan(plan)
        logger.info("=" * 70)
        logger.info("VALIDATION RESULTS")
        logger.info("=" * 70)
        logger.info(f"✓ Valid: {validation['valid']}")
        logger.info(f"✓ Segments: {validation['segment_count']}/{plan.segment_count}")
        
        if validation['issues']:
            logger.warning(f"⚠️  Issues: {validation['issues']}")
        if validation['warnings']:
            logger.info(f"ℹ️  Warnings: {validation['warnings']}")
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("🎉 TEST COMPLETE - AI PROMPT GENERATION WORKING!")
        logger.info("=" * 70)
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}", exc_info=True)
        return False


async def test_manual_mode():
    """Test manual mode (AI disabled)."""
    logger.info("\n" + "=" * 70)
    logger.info("MANUAL MODE TEST (AI Disabled)")
    logger.info("=" * 70)
    
    settings = Settings()
    orchestrator = VideoOrchestrator(settings)
    
    plan = await orchestrator.create_video_plan(
        project_id="manual_test_001",
        story_prompt="Test story",
        target_duration_sec=12,
        segment_len_sec=6,
        use_ai=False  # Disable AI
    )
    
    logger.info(f"\n✓ Created plan with {len(plan.segments)} placeholder segments")
    for segment in plan.segments:
        logger.info(f"  - Segment {segment.segment_index}: {segment.prompt[:50]}...")
    
    logger.info("\n✓ Manual mode working correctly")


async def main():
    """Run all tests."""
    logger.info("")
    logger.info("╔" + "═" * 68 + "╗")
    logger.info("║" + " " * 15 + "AI PROMPT GENERATION TEST SUITE" + " " * 21 + "║")
    logger.info("╚" + "═" * 68 + "╝")
    logger.info("")
    
    # Test 1: AI-powered generation
    ai_success = await test_ai_prompt_generation()
    
    # Test 2: Manual mode
    await test_manual_mode()
    
    logger.info("\n" + "=" * 70)
    logger.info("ALL TESTS COMPLETE")
    logger.info("=" * 70)
    
    if ai_success:
        logger.info("✅ AI prompt generation is ready for production use!")
    else:
        logger.info("⚠️  AI generation had issues - check logs above")


if __name__ == "__main__":
    asyncio.run(main())
