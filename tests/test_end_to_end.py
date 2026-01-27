"""End-to-end workflow test with complete video creation pipeline."""

import asyncio
import logging
import os
from pathlib import Path

import pytest

from src.config import Settings
from src.core.orchestrator import VideoOrchestrator
from src.models.segment import SegmentStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestEndToEndWorkflow:
    """End-to-end workflow tests for complete video creation."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow_without_mcp(self, orchestrator, sample_story_prompt):
        """Test complete workflow without MCP tools (architecture validation)."""
        logger.info("="*70)
        logger.info("E2E TEST: Complete Workflow (No MCP)")
        logger.info("="*70)
        
        # Step 1: Create video plan
        logger.info("\nStep 1: Creating video plan...")
        plan = await orchestrator.create_video_plan(
            project_id="e2e_test_001",
            story_prompt=sample_story_prompt,
            target_duration_sec=12,
            segment_len_sec=6,
            use_ai=False  # Disable AI for faster testing
        )
        
        assert plan is not None
        assert plan.segment_count == 2
        assert len(plan.segments) == 2
        logger.info(f"✓ Video plan created with {plan.segment_count} segments")
        
        # Step 2: Validate plan
        logger.info("\nStep 2: Validating plan...")
        validation = orchestrator.validate_plan(plan)
        
        assert validation['valid'] is True
        logger.info(f"✓ Plan validation passed")
        
        # Step 3: Save plan
        logger.info("\nStep 3: Saving plan...")
        save_path = await orchestrator.save_plan(plan)
        
        assert save_path.exists()
        logger.info(f"✓ Plan saved to {save_path}")
        
        # Step 4: Load plan
        logger.info("\nStep 4: Loading plan...")
        loaded_plan = await orchestrator.load_plan(save_path)
        
        assert loaded_plan.project_id == plan.project_id
        logger.info(f"✓ Plan loaded successfully")
        
        # Step 5: Simulate segment approval
        logger.info("\nStep 5: Simulating segment approval...")
        for segment in loaded_plan.segments:
            segment.approved = True
        
        approved_count = sum(1 for s in loaded_plan.segments if s.approved)
        assert approved_count == loaded_plan.segment_count
        logger.info(f"✓ All {approved_count} segments approved")
        
        logger.info("\n" + "="*70)
        logger.info("✅ E2E TEST PASSED (Architecture Validated)")
        logger.info("="*70)
    
    @pytest.mark.asyncio
    async def test_workflow_with_ai_prompts(self, orchestrator, sample_story_prompt):
        """Test workflow with AI-generated prompts (requires OPENAI_API_KEY)."""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set - skipping AI test")
        
        logger.info("="*70)
        logger.info("E2E TEST: Workflow with AI Prompts")
        logger.info("="*70)
        
        # Create plan with AI
        logger.info("\nGenerating AI-powered video plan...")
        plan = await orchestrator.create_video_plan(
            project_id="e2e_ai_test",
            story_prompt=sample_story_prompt,
            target_duration_sec=12,
            segment_len_sec=6,
            use_ai=True
        )
        
        assert plan is not None
        assert len(plan.segments) == 2
        
        # Verify AI generated meaningful prompts
        for i, segment in enumerate(plan.segments):
            logger.info(f"\nSegment {i}:")
            logger.info(f"  Prompt: {segment.prompt[:80]}...")
            logger.info(f"  Narration: {segment.narration_text[:80]}...")
            
            # AI prompts should not be placeholders
            assert not segment.prompt.startswith("[Segment")
            assert not segment.narration_text.startswith("[Segment")
            assert len(segment.prompt) > 30
        
        logger.info("\n" + "="*70)
        logger.info("✅ AI PROMPTS TEST PASSED")
        logger.info("="*70)
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, orchestrator):
        """Test error handling in workflow."""
        logger.info("="*70)
        logger.info("E2E TEST: Error Handling")
        logger.info("="*70)
        
        # Test 1: Invalid duration
        logger.info("\nTest 1: Invalid duration (>60s)...")
        with pytest.raises(AssertionError, match="Target duration must be"):
            await orchestrator.create_video_plan(
                project_id="error_test_1",
                story_prompt="test",
                target_duration_sec=100,  # Invalid
                segment_len_sec=6
            )
        logger.info("✓ Correctly rejected invalid duration")
        
        # Test 2: Invalid segment length
        logger.info("\nTest 2: Invalid segment length...")
        with pytest.raises(AssertionError, match="Segment length must be"):
            await orchestrator.create_video_plan(
                project_id="error_test_2",
                story_prompt="test",
                target_duration_sec=12,
                segment_len_sec=5  # Invalid
            )
        logger.info("✓ Correctly rejected invalid segment length")
        
        # Test 3: Finalize without approved segments
        logger.info("\nTest 3: Finalize without approved segments...")
        plan = await orchestrator.create_video_plan(
            project_id="error_test_3",
            story_prompt="test",
            target_duration_sec=12,
            segment_len_sec=6,
            use_ai=False
        )
        
        with pytest.raises(ValueError, match="not approved"):
            await orchestrator.finalize_video(plan)
        logger.info("✓ Correctly rejected finalization of unapproved segments")
        
        logger.info("\n" + "="*70)
        logger.info("✅ ERROR HANDLING TEST PASSED")
        logger.info("="*70)
    
    @pytest.mark.asyncio
    async def test_workflow_different_configurations(self, orchestrator, sample_story_prompt):
        """Test workflow with different segment configurations."""
        logger.info("="*70)
        logger.info("E2E TEST: Different Configurations")
        logger.info("="*70)
        
        configurations = [
            {"duration": 6, "segment_len": 6, "expected_segments": 1},
            {"duration": 12, "segment_len": 6, "expected_segments": 2},
            {"duration": 30, "segment_len": 6, "expected_segments": 5},
            {"duration": 60, "segment_len": 6, "expected_segments": 10},
            {"duration": 10, "segment_len": 10, "expected_segments": 1},
            {"duration": 30, "segment_len": 10, "expected_segments": 3},
            {"duration": 60, "segment_len": 10, "expected_segments": 6},
        ]
        
        for i, config in enumerate(configurations):
            logger.info(f"\nConfiguration {i+1}: {config['duration']}s with {config['segment_len']}s segments")
            
            plan = await orchestrator.create_video_plan(
                project_id=f"config_test_{i}",
                story_prompt=sample_story_prompt,
                target_duration_sec=config['duration'],
                segment_len_sec=config['segment_len'],
                use_ai=False
            )
            
            assert plan.segment_count == config['expected_segments']
            assert len(plan.segments) == config['expected_segments']
            
            validation = orchestrator.validate_plan(plan)
            assert validation['valid'] is True
            
            logger.info(f"  ✓ Created {plan.segment_count} segments successfully")
        
        logger.info("\n" + "="*70)
        logger.info("✅ CONFIGURATION TEST PASSED")
        logger.info("="*70)


@pytest.mark.asyncio
async def test_full_pipeline_simulation():
    """Simulate full pipeline without external dependencies."""
    logger.info("\n" + "="*70)
    logger.info("FULL PIPELINE SIMULATION")
    logger.info("="*70)
    
    # Initialize
    settings = Settings()
    orchestrator = VideoOrchestrator(settings)
    
    story = "A serene journey through a mystical forest at dawn"
    
    # Phase 1: Planning
    logger.info("\n📋 PHASE 1: Planning")
    logger.info("-" * 70)
    
    plan = await orchestrator.create_video_plan(
        project_id="full_pipeline_test",
        story_prompt=story,
        target_duration_sec=12,
        segment_len_sec=6,
        use_ai=False
    )
    
    logger.info(f"✓ Created plan: {plan.segment_count} segments")
    
    # Phase 2: Validation
    logger.info("\n✅ PHASE 2: Validation")
    logger.info("-" * 70)
    
    validation = orchestrator.validate_plan(plan)
    assert validation['valid']
    logger.info(f"✓ Validation passed: {validation}")
    
    # Phase 3: Segment Processing (simulated)
    logger.info("\n🎬 PHASE 3: Segment Processing (Simulated)")
    logger.info("-" * 70)
    
    for i, segment in enumerate(plan.segments):
        logger.info(f"\nProcessing segment {i}:")
        logger.info(f"  Prompt: {segment.prompt[:60]}...")
        logger.info(f"  Narration: {segment.narration_text[:60]}...")
        
        # Simulate processing
        segment.first_frame_image_url = f"storage/projects/seg_{i}_first.jpg"
        segment.last_frame_image_url = f"storage/projects/seg_{i}_last.jpg"
        segment.segment_video_url = f"storage/projects/seg_{i}_video.mp4"
        segment.segment_audio_url = f"storage/projects/seg_{i}_audio.mp3"
        segment.video_duration_sec = 6.0
        segment.approved = True
        
        logger.info(f"  ✓ Segment {i} processed and approved")
    
    # Phase 4: Persistence
    logger.info("\n💾 PHASE 4: Persistence")
    logger.info("-" * 70)
    
    save_path = await orchestrator.save_plan(plan)
    logger.info(f"✓ Plan saved: {save_path}")
    
    loaded = await orchestrator.load_plan(save_path)
    assert loaded.project_id == plan.project_id
    logger.info(f"✓ Plan loaded successfully")
    
    # Phase 5: Final validation
    logger.info("\n🎯 PHASE 5: Final Validation")
    logger.info("-" * 70)
    
    final_validation = orchestrator.validate_plan(loaded)
    assert final_validation['valid']
    assert final_validation['approved_count'] == loaded.segment_count
    logger.info(f"✓ All segments approved: {final_validation['approved_count']}/{final_validation['segment_count']}")
    
    logger.info("\n" + "="*70)
    logger.info("🎉 FULL PIPELINE SIMULATION COMPLETE")
    logger.info("="*70)
    logger.info("\nSummary:")
    logger.info(f"  - Project: {loaded.project_id}")
    logger.info(f"  - Duration: {loaded.target_duration_sec}s")
    logger.info(f"  - Segments: {loaded.segment_count}")
    logger.info(f"  - All approved: {final_validation['approved_count'] == loaded.segment_count}")
    logger.info("="*70)


if __name__ == "__main__":
    # Run async test
    asyncio.run(test_full_pipeline_simulation())
