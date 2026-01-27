"""Pytest configuration and shared fixtures for testing."""

import asyncio
import os
import tempfile
from pathlib import Path

import pytest
from dotenv import load_dotenv

from src.config import Settings
from src.core.orchestrator import VideoOrchestrator

# Load environment variables
load_dotenv()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """Provide test settings with temporary directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        settings = Settings(
            project_root_path=Path(tmpdir) / "projects",
            temp_folder=Path(tmpdir) / "temp",
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            minimax_api_key=os.getenv("MINIMAX_API_KEY", ""),
        )
        yield settings


@pytest.fixture
async def orchestrator(test_settings):
    """Provide a VideoOrchestrator instance."""
    return VideoOrchestrator(test_settings)


@pytest.fixture
def sample_story_prompt():
    """Sample story prompt for testing."""
    return "A peaceful sunrise over the ocean, with waves gently lapping at the shore"


@pytest.fixture
def sample_audio_bytes():
    """Generate sample audio bytes for testing (WAV format)."""
    # Simple WAV header + silence
    sample_rate = 44100
    duration_sec = 1
    num_samples = sample_rate * duration_sec
    
    # WAV file header (44 bytes)
    wav_header = bytes([
        0x52, 0x49, 0x46, 0x46,  # "RIFF"
        0x00, 0x00, 0x00, 0x00,  # File size (will be filled)
        0x57, 0x41, 0x56, 0x45,  # "WAVE"
        0x66, 0x6D, 0x74, 0x20,  # "fmt "
        0x10, 0x00, 0x00, 0x00,  # Subchunk1Size (16 for PCM)
        0x01, 0x00,              # AudioFormat (1 = PCM)
        0x01, 0x00,              # NumChannels (1 = mono)
        0x44, 0xAC, 0x00, 0x00,  # SampleRate (44100)
        0x88, 0x58, 0x01, 0x00,  # ByteRate
        0x02, 0x00,              # BlockAlign
        0x10, 0x00,              # BitsPerSample (16)
        0x64, 0x61, 0x74, 0x61,  # "data"
        0x00, 0x00, 0x00, 0x00,  # Subchunk2Size (will be filled)
    ])
    
    # Generate silence (all zeros)
    audio_data = bytes([0] * (num_samples * 2))  # 2 bytes per sample (16-bit)
    
    # Update sizes in header
    file_size = len(wav_header) + len(audio_data) - 8
    data_size = len(audio_data)
    
    wav_header_list = list(wav_header)
    # Update file size
    wav_header_list[4:8] = file_size.to_bytes(4, 'little')
    # Update data size
    wav_header_list[40:44] = data_size.to_bytes(4, 'little')
    
    return bytes(wav_header_list) + audio_data


@pytest.fixture
def sample_video_plan():
    """Sample video plan data for testing."""
    return {
        "project_id": "test_project_001",
        "target_duration_sec": 12,
        "segment_len_sec": 6,
        "segment_count": 2,
    }
