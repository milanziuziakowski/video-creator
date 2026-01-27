"""Test voice cloning implementation.

This script tests the MiniMax voice cloning functionality in the orchestrator.
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


async def test_voice_clone():
    """Test voice cloning from audio sample."""
    logger.info("=" * 70)
    logger.info("VOICE CLONING TEST")
    logger.info("=" * 70)
    
    # Initialize
    settings = Settings()
    orchestrator = VideoOrchestrator(settings)
    
    # Check if MiniMax API key is configured
    if not settings.minimax_api_key:
        logger.error("❌ MINIMAX_API_KEY not set in environment")
        logger.info("Please set MINIMAX_API_KEY in .env file")
        logger.info("\nExample .env:")
        logger.info("MINIMAX_API_KEY=your_api_key_here")
        return
    
    logger.info("✓ MiniMax API key configured")
    
    # Test with a sample audio file (if exists)
    test_audio_path = Path("storage/temp/test_voice_sample.wav")
    
    if not test_audio_path.exists():
        logger.warning(f"⚠️  Test audio file not found: {test_audio_path}")
        logger.info("\nTo test voice cloning:")
        logger.info("1. Place a voice sample (WAV, MP3, or M4A) at:")
        logger.info(f"   {test_audio_path}")
        logger.info("2. Audio should be 10 seconds to 5 minutes")
        logger.info("3. Max file size: 20MB")
        logger.info("4. Run this script again")
        return
    
    try:
        # Read audio bytes
        with open(test_audio_path, 'rb') as f:
            audio_bytes = f.read()
        
        logger.info(f"\n📁 Audio file: {test_audio_path}")
        logger.info(f"   Size: {len(audio_bytes) / 1024:.1f} KB")
        
        # Clone voice
        logger.info("\n🎤 Cloning voice...")
        voice_id = await orchestrator.clone_voice(
            voice_sample_bytes=audio_bytes,
            voice_name="test_voice"
        )
        
        if voice_id:
            logger.info(f"\n✅ SUCCESS!")
            logger.info(f"   Voice ID: {voice_id}")
            logger.info(f"\nYou can now use this voice_id for text-to-speech generation.")
            logger.info(f"Note: Voice will expire after 7 days unless used for synthesis.")
        else:
            logger.error(f"\n❌ Voice cloning failed")
            logger.info("Check the logs above for error details")
    
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(test_voice_clone())
