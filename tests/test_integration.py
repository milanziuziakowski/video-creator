"""Integration tests for core functionality."""

import pytest
from pathlib import Path

from src.models.segment import SegmentStatus
from src.models.video_plan import VideoPlan


class TestDataModels:
    """Test data model validation and serialization."""
    
    def test_segment_status_creation(self):
        """Test SegmentStatus model creation."""
        segment = SegmentStatus(
            segment_index=0,
            prompt="Test video prompt",
            narration_text="Test narration text"
        )
        
        assert segment.segment_index == 0
        assert segment.prompt == "Test video prompt"
        assert segment.narration_text == "Test narration text"
        assert segment.approved is False
        assert segment.first_frame_image_url is None
    
    def test_segment_status_json_serialization(self):
        """Test SegmentStatus JSON serialization."""
        segment = SegmentStatus(
            segment_index=1,
            prompt="Test prompt",
            narration_text="Test narration"
        )
        
        json_str = segment.model_dump_json()
        assert "segment_index" in json_str
        assert "Test prompt" in json_str
        
        # Test deserialization
        segment2 = SegmentStatus.model_validate_json(json_str)
        assert segment2.segment_index == segment.segment_index
        assert segment2.prompt == segment.prompt
    
    def test_video_plan_creation(self, sample_video_plan):
        """Test VideoPlan model creation."""
        plan = VideoPlan(**sample_video_plan)
        
        assert plan.project_id == "test_project_001"
        assert plan.target_duration_sec == 12
        assert plan.segment_len_sec == 6
        assert plan.segment_count == 2
        assert len(plan.segments) == 0
    
    def test_video_plan_with_segments(self):
        """Test VideoPlan with segments."""
        segment1 = SegmentStatus(
            segment_index=0,
            prompt="First segment",
            narration_text="First narration"
        )
        segment2 = SegmentStatus(
            segment_index=1,
            prompt="Second segment",
            narration_text="Second narration"
        )
        
        plan = VideoPlan(
            project_id="test_001",
            target_duration_sec=12,
            segment_len_sec=6,
            segment_count=2,
            segments=[segment1, segment2]
        )
        
        assert len(plan.segments) == 2
        assert plan.segments[0].segment_index == 0
        assert plan.segments[1].segment_index == 1


class TestOrchestrator:
    """Test orchestrator functionality."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initializes correctly."""
        assert orchestrator is not None
        assert orchestrator.settings is not None
        assert orchestrator.settings.project_root_path.exists()
        assert orchestrator.settings.temp_folder.exists()
    
    @pytest.mark.asyncio
    async def test_create_video_plan_without_ai(self, orchestrator, sample_story_prompt):
        """Test video plan creation without AI."""
        plan = await orchestrator.create_video_plan(
            project_id="test_no_ai",
            story_prompt=sample_story_prompt,
            target_duration_sec=12,
            segment_len_sec=6,
            use_ai=False
        )
        
        assert plan.project_id == "test_no_ai"
        assert plan.target_duration_sec == 12
        assert plan.segment_len_sec == 6
        assert plan.segment_count == 2
        assert len(plan.segments) == 2
        
        # Segments should have placeholder prompts when AI is disabled
        for segment in plan.segments:
            assert segment.prompt.startswith("[Segment")
            assert segment.narration_text.startswith("[Segment")
    
    @pytest.mark.asyncio
    async def test_create_video_plan_with_ai(self, orchestrator, sample_story_prompt):
        """Test video plan creation with AI (requires OPENAI_API_KEY)."""
        import os
        
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")
        
        plan = await orchestrator.create_video_plan(
            project_id="test_with_ai",
            story_prompt=sample_story_prompt,
            target_duration_sec=12,
            segment_len_sec=6,
            use_ai=True
        )
        
        assert plan.project_id == "test_with_ai"
        assert plan.segment_count == 2
        assert len(plan.segments) == 2
        
        # AI-generated prompts should not be placeholders
        for segment in plan.segments:
            assert not segment.prompt.startswith("[Segment")
            assert not segment.narration_text.startswith("[Segment")
            assert len(segment.prompt) > 20  # Should be descriptive
    
    @pytest.mark.asyncio
    async def test_validate_plan(self, orchestrator):
        """Test video plan validation."""
        # Create valid plan
        plan = VideoPlan(
            project_id="test_validation",
            target_duration_sec=12,
            segment_len_sec=6,
            segment_count=2,
            segments=[
                SegmentStatus(segment_index=0, prompt="Prompt 1", narration_text="Narration 1"),
                SegmentStatus(segment_index=1, prompt="Prompt 2", narration_text="Narration 2"),
            ]
        )
        
        validation = orchestrator.validate_plan(plan)
        
        assert validation['valid'] is True
        assert validation['segment_count'] == 2
        assert validation['approved_count'] == 0
        assert len(validation['issues']) == 0
    
    @pytest.mark.asyncio
    async def test_validate_plan_invalid_duration(self, orchestrator):
        """Test validation fails for invalid duration."""
        plan = VideoPlan(
            project_id="test_invalid",
            target_duration_sec=100,  # Exceeds 60s limit
            segment_len_sec=6,
            segment_count=2,
        )
        
        validation = orchestrator.validate_plan(plan)
        
        assert validation['valid'] is False
        assert any("60s limit" in issue for issue in validation['issues'])
    
    @pytest.mark.asyncio
    async def test_validate_plan_invalid_segment_length(self, orchestrator):
        """Test validation fails for invalid segment length."""
        plan = VideoPlan(
            project_id="test_invalid_seg",
            target_duration_sec=12,
            segment_len_sec=5,  # Invalid - must be 6 or 10
            segment_count=2,
        )
        
        validation = orchestrator.validate_plan(plan)
        
        assert validation['valid'] is False
        assert any("must be 6 or 10" in issue for issue in validation['issues'])
    
    @pytest.mark.asyncio
    async def test_save_and_load_plan(self, orchestrator, tmp_path):
        """Test saving and loading video plans."""
        # Create plan
        plan = VideoPlan(
            project_id="test_save_load",
            target_duration_sec=12,
            segment_len_sec=6,
            segment_count=2,
            segments=[
                SegmentStatus(segment_index=0, prompt="Prompt 1", narration_text="Narration 1")
            ]
        )
        
        # Save plan
        save_path = tmp_path / "plan.json"
        saved_path = await orchestrator.save_plan(plan, save_path)
        
        assert saved_path.exists()
        
        # Load plan
        loaded_plan = await orchestrator.load_plan(saved_path)
        
        assert loaded_plan.project_id == plan.project_id
        assert loaded_plan.target_duration_sec == plan.target_duration_sec
        assert len(loaded_plan.segments) == len(plan.segments)
        assert loaded_plan.segments[0].prompt == plan.segments[0].prompt


class TestStorage:
    """Test storage functionality."""
    
    @pytest.mark.asyncio
    async def test_local_storage_upload(self, tmp_path):
        """Test local storage upload."""
        from utils.storage import LocalStorage
        
        storage = LocalStorage(base_path=str(tmp_path / "storage"))
        
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Upload
        url = await storage.upload_file(str(test_file), "test_upload.txt")
        
        assert "test_upload.txt" in url
        assert await storage.exists("test_upload.txt")
    
    @pytest.mark.asyncio
    async def test_local_storage_download(self, tmp_path):
        """Test local storage download."""
        from utils.storage import LocalStorage
        
        storage = LocalStorage(base_path=str(tmp_path / "storage"))
        
        # Create and upload file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        await storage.upload_file(str(test_file), "test.txt")
        
        # Download
        download_path = tmp_path / "downloaded.txt"
        await storage.download_file("test.txt", str(download_path))
        
        assert download_path.exists()
        assert download_path.read_text() == "test content"
    
    @pytest.mark.asyncio
    async def test_local_storage_delete(self, tmp_path):
        """Test local storage delete."""
        from utils.storage import LocalStorage
        
        storage = LocalStorage(base_path=str(tmp_path / "storage"))
        
        # Create and upload file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        await storage.upload_file(str(test_file), "test.txt")
        
        assert await storage.exists("test.txt")
        
        # Delete
        await storage.delete_file("test.txt")
        
        assert not await storage.exists("test.txt")


class TestAIPromptGenerator:
    """Test AI prompt generation."""
    
    @pytest.mark.asyncio
    async def test_default_prompts_generation(self):
        """Test fallback default prompt generation."""
        from src.ai.prompt_generator import create_default_prompts
        
        story_plan = create_default_prompts("A sunset over mountains", segment_count=2)
        
        assert story_plan.title is not None
        assert len(story_plan.segments) == 2
        assert story_plan.segments[0].segment_index == 0
        assert story_plan.segments[1].segment_index == 1
        assert "sunset" in story_plan.segments[0].video_prompt.lower()
