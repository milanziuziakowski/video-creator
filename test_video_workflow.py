"""End-to-end workflow test for video creator.

NOTE: MCP tools (mcp_minimax, mcp_mediaops, mcp_fl2v) cannot be imported as Python packages.
They're only accessible via MCP protocol (e.g., in VS Code Copilot).

This script tests the orchestrator which internally calls MCP tools via the protocol.
To run actual MCP tool tests, use the MCP servers directly or test via VS Code Copilot.
"""

import asyncio
import logging
from pathlib import Path
import tempfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def workflow_test_orchestrator_init():
    """Test 1: Orchestrator initialization."""
    logger.info("\n" + "="*70)
    logger.info("TEST 1: Orchestrator Initialization")
    logger.info("="*70)
    
    try:
        from src.config import Settings
        from src.core.orchestrator import VideoOrchestrator
        
        settings = Settings()
        orchestrator = VideoOrchestrator(settings)
        
        logger.info("✓ Orchestrator initialized")
        logger.info(f"  - Settings loaded: {settings.model_dump_json()[:100]}...")
        
        return {
            'success': True,
            'orchestrator': orchestrator
        }
        
    except Exception as e:
        logger.error(f"✗ Orchestrator initialization failed: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


async def workflow_test_video_plan():
    """Test 2: Video plan generation with AI."""
    logger.info("\n" + "="*70)
    logger.info("TEST 2: Video Plan Generation (AI Prompts)")
    logger.info("="*70)
    
    try:
        from src.config import Settings
        from src.core.orchestrator import VideoOrchestrator
        
        settings = Settings()
        orchestrator = VideoOrchestrator(settings)
        
        # Create a video plan
        logger.info("Creating video plan...")
        plan = await orchestrator.create_video_plan(
            project_id="test_project_001",
            story_prompt="A sunrise over the ocean",
            target_duration_sec=12,
            segment_len_sec=6
        )
        
        logger.info(f"✓ Video plan created:")
        logger.info(f"  - Project: {plan.project_id}")
        logger.info(f"  - Duration: {plan.target_duration_sec}s")
        logger.info(f"  - Segments: {plan.segment_count}")
        logger.info(f"  - Segment length: {plan.segment_len_sec}s")
        
        for i, segment in enumerate(plan.segments):
            logger.info(f"  - Segment {i}: {segment.prompt[:60]}...")
        
        return {
            'success': True,
            'plan': plan
        }
        
    except Exception as e:
        logger.error(f"✗ Video plan generation failed: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


async def workflow_test_storage():
    """Test 3: Storage configuration."""
    logger.info("\n" + "="*70)
    logger.info("TEST 3: Storage Configuration")
    logger.info("="*70)
    
    try:
        from utils.storage import get_storage_path
        
        # Test storage paths
        project_id = "test_project_001"
        
        project_dir = get_storage_path(project_id)
        frames_dir = get_storage_path(project_id, "frames")
        videos_dir = get_storage_path(project_id, "videos")
        audio_dir = get_storage_path(project_id, "audio")
        
        logger.info("✓ Storage paths configured:")
        logger.info(f"  - Project: {project_dir}")
        logger.info(f"  - Frames: {frames_dir}")
        logger.info(f"  - Videos: {videos_dir}")
        logger.info(f"  - Audio: {audio_dir}")
        
        return {'success': True}
        
    except Exception as e:
        logger.error(f"✗ Storage configuration failed: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


async def workflow_test_models():
    """Test 4: Data models validation."""
    logger.info("\n" + "="*70)
    logger.info("TEST 4: Data Models Validation")
    logger.info("="*70)
    
    try:
        from src.models.segment import Segment
        from src.models.video_plan import VideoPlan
        
        # Create test segment
        segment = Segment(
            index=0,
            prompt="Test prompt",
            first_frame_prompt="First frame",
            last_frame_prompt="Last frame",
            narration="Test narration"
        )
        
        # Create test plan
        plan = VideoPlan(
            project_id="test_001",
            target_duration_sec=10,
            segment_len_sec=5,
            segment_count=2,
            segments=[segment]
        )
        
        logger.info("✓ Data models validated:")
        logger.info(f"  - Segment: {segment.model_dump_json()[:80]}...")
        logger.info(f"  - VideoPlan: {plan.model_dump_json()[:80]}...")
        
        return {'success': True}
        
    except Exception as e:
        logger.error(f"✗ Data models validation failed: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


async def workflow_test_mcp_integration_info():
    """Test 5: MCP integration information."""
    logger.info("\n" + "="*70)
    logger.info("TEST 5: MCP Integration Information")
    logger.info("="*70)
    
    try:
        logger.info("MCP Servers available in this project:")
        logger.info("  1. minimax_mcp - Text-to-image, text-to-audio, voice cloning, video generation")
        logger.info("  2. fl2v_mcp - First-last frame to video generation")
        logger.info("  3. mediaops_mcp - FFmpeg operations (concat, mux, extract, normalize)")
        logger.info("")
        logger.info("To test MCP tools:")
        logger.info("  - Start MCP servers (see mcp_servers/*/README.md)")
        logger.info("  - Use MCP protocol client (e.g., VS Code Copilot)")
        logger.info("  - Or test via orchestrator methods which call MCP tools internally")
        logger.info("")
        logger.info("Orchestrator methods that use MCP tools:")
        logger.info("  - clone_voice() -> calls mcp_minimax voice_clone")
        logger.info("  - clone_voice_from_video() -> calls mediaops + voice_clone")
        logger.info("  - (Future) generate_frames() -> will call text_to_image")
        logger.info("  - (Future) generate_audio() -> will call text_to_audio")
        logger.info("  - (Future) generate_video_segment() -> will call fl2v")
        
        return {'success': True}
        
    except Exception as e:
        logger.error(f"✗ MCP integration info failed: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}




async def main():
    """Run complete workflow test."""
    logger.info("="*70)
    logger.info("VIDEO CREATOR - ARCHITECTURE VALIDATION TEST")
    logger.info("="*70)
    logger.info("NOTE: This validates architecture components, not MCP tool calls.")
    logger.info("MCP tools require MCP protocol - test via orchestrator or VS Code Copilot.")
    logger.info("="*70)
    
    results = {}
    
    # Test 1: Orchestrator Init
    orch_init = await workflow_test_orchestrator_init()
    results['orchestrator_init'] = orch_init['success']
    
    # Test 2: Video Plan
    plan_result = await workflow_test_video_plan()
    results['video_plan'] = plan_result['success']
    
    # Test 3: Storage
    storage_result = await workflow_test_storage()
    results['storage'] = storage_result['success']
    
    # Test 4: Models
    models_result = await workflow_test_models()
    results['models'] = models_result['success']
    
    # Test 5: MCP Info
    mcp_result = await workflow_test_mcp_integration_info()
    results['mcp_info'] = mcp_result['success']
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("WORKFLOW TEST SUMMARY")
    logger.info("="*70)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {test_name.replace('_', ' ').title()}")
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    logger.info(f"\nTotal: {passed_count}/{total_count} tests passed")
    logger.info("="*70)
    
    if passed_count == total_count:
        logger.info("\n🎉 All architecture tests PASSED!")
        logger.info("\nNext steps:")
        logger.info("  1. Start MCP servers to test actual tool calls")
        logger.info("  2. Test orchestrator methods that call MCP tools")
        logger.info("  3. Run end-to-end video creation workflow")
    else:
        logger.info("\n⚠️  Some tests failed. Review logs above for details.")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
