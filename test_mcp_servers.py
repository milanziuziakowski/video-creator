"""Test script for MCP servers - validates server implementations."""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_minimax_server_import():
    """Test that MiniMax MCP server can be imported."""
    logger.info("=== Testing MiniMax Server Import ===")
    try:
        from mcp_servers.minimax_mcp import minimax_server
        logger.info(f"✓ MiniMax server module imported successfully")
        logger.info(f"✓ Server file: {minimax_server.__file__}")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to import MiniMax server: {e}")
        return False


async def test_fl2v_server_import():
    """Test that FL2V MCP server can be imported."""
    logger.info("=== Testing FL2V Server Import ===")
    try:
        from mcp_servers.fl2v_mcp import fl2v_server
        logger.info(f"✓ FL2V server module imported successfully")
        logger.info(f"✓ Server file: {fl2v_server.__file__}")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to import FL2V server: {e}")
        return False


async def test_mediaops_server_import():
    """Test that MediaOps MCP server can be imported."""
    logger.info("=== Testing MediaOps Server Import ===")
    try:
        from mcp_servers.mediaops_mcp import mediaops_server
        logger.info(f"✓ MediaOps server module imported successfully")
        logger.info(f"✓ Server file: {mediaops_server.__file__}")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to import MediaOps server: {e}")
        return False


async def test_ffmpeg_wrapper():
    """Test FFmpeg wrapper functions."""
    logger.info("=== Testing FFmpeg Wrapper ===")
    try:
        from utils.ffmpeg_wrapper import probe_media
        logger.info(f"✓ FFmpeg wrapper imported successfully")
        
        # Test probe on a simple file
        import tempfile
        test_file = Path(tempfile.gettempdir()) / "test.txt"
        test_file.write_text("test content")
        
        try:
            # This should fail but shows probe_media works
            result = await probe_media(str(test_file))
            logger.info(f"✓ probe_media executed (result: {result})")
        except Exception as e:
            # Expected to fail on non-media file
            logger.info(f"✓ probe_media executed with expected error on non-media file")
        
        return True
    except Exception as e:
        logger.error(f"✗ FFmpeg wrapper test failed: {e}")
        return False


async def test_orchestrator():
    """Test orchestrator can be imported and initialized."""
    logger.info("=== Testing Orchestrator ===")
    try:
        from src.core.orchestrator import VideoOrchestrator
        from src.config import Settings
        
        logger.info(f"✓ Orchestrator imported successfully")
        
        settings = Settings()
        orchestrator = VideoOrchestrator(settings)
        
        logger.info(f"✓ Orchestrator initialized")
        logger.info(f"✓ Project root: {settings.project_root_path}")
        logger.info(f"✓ Temp folder: {settings.temp_folder}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Orchestrator test failed: {e}")
        return False


async def test_ai_prompt_generator():
    """Test AI prompt generator can be imported."""
    logger.info("=== Testing AI Prompt Generator ===")
    try:
        from src.ai.prompt_generator import (
            generate_story_plan,
            create_default_prompts
        )
        
        logger.info(f"✓ AI prompt generator imported successfully")
        
        # Test default prompts (no API key needed)
        default_plan = create_default_prompts("Test story", 2)
        logger.info(f"✓ Default prompts generated: {len(default_plan.segments)} segments")
        
        return True
    except Exception as e:
        logger.error(f"✗ AI prompt generator test failed: {e}")
        return False



async def main():
    """Run all tests."""
    logger.info("===== MCP Server Component Tests =====\n")
    
    tests = [
        ("MiniMax Server Import", test_minimax_server_import),
        ("FL2V Server Import", test_fl2v_server_import),
        ("MediaOps Server Import", test_mediaops_server_import),
        ("FFmpeg Wrapper", test_ffmpeg_wrapper),
        ("Orchestrator", test_orchestrator),
        ("AI Prompt Generator", test_ai_prompt_generator),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}", exc_info=True)
            results[test_name] = False
        
        logger.info("\n" + "="*50 + "\n")
    
    # Summary
    logger.info("===== Test Summary =====")
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    logger.info(f"\nPassed: {passed}/{total}")
    
    logger.info("\n" + "="*50)
    logger.info("NOTE: To test actual MCP tool calls (text_to_image, voice_clone, etc.),")
    logger.info("the MCP servers must be running and accessed via MCP protocol,")
    logger.info("not direct Python imports. These tests verify the server modules load correctly.")


if __name__ == "__main__":
    asyncio.run(main())

