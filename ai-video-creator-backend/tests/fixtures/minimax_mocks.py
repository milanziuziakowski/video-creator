"""MiniMax API mock fixtures using real captured responses."""

import json
from pathlib import Path
from typing import Any

# Load real MiniMax API responses
FIXTURES_DIR = Path(__file__).parent
MINIMAX_RESPONSES_FILE = FIXTURES_DIR / "minimax_real_responses.json"

with open(MINIMAX_RESPONSES_FILE) as f:
    MINIMAX_REAL_RESPONSES: dict[str, Any] = json.load(f)


def get_files_upload_response() -> dict[str, Any]:
    """Get real file upload response."""
    return {
        "base_resp": {"status_code": 0, "status_msg": "success"},
        "file": {"file_id": str(MINIMAX_REAL_RESPONSES["files_upload"]["response"]["file_id"])},
    }


def get_voice_clone_response() -> dict[str, Any]:
    """Get real voice clone response."""
    return {"base_resp": {"status_code": 0, "status_msg": "success"}}


def get_voice_clone_request() -> dict[str, Any]:
    """Get real voice clone request parameters."""
    return MINIMAX_REAL_RESPONSES["voice_clone"]["request"]


def get_t2a_v2_response() -> dict[str, Any]:
    """Get real text-to-audio response.

    Note: Returns base64 encoded audio data. The real response was 44,160 bytes.
    For testing, we return a minimal valid MP3.
    """
    # Minimal valid MP3 header (ID3v2 + MPEG frame)
    mp3_bytes = b"\xff\xfb\x90\x00" + b"\x00" * 100
    import base64

    return {
        "base_resp": {"status_code": 0, "status_msg": "success"},
        "data": {"audio": base64.b64encode(mp3_bytes).decode("utf-8")},
    }


def get_t2a_v2_request() -> dict[str, Any]:
    """Get real text-to-audio request parameters."""
    return MINIMAX_REAL_RESPONSES["t2a_v2"]["request"]


def get_video_generation_response() -> dict[str, Any]:
    """Get video generation task creation response."""
    return {"base_resp": {"status_code": 0, "status_msg": "success"}, "task_id": "mock-task-12345"}


def get_query_video_generation_processing() -> dict[str, Any]:
    """Get video generation status response (processing)."""
    return {
        "base_resp": {"status_code": 0, "status_msg": "success"},
        "task_id": "mock-task-12345",
        "status": "Processing",
    }


def get_query_video_generation_success() -> dict[str, Any]:
    """Get video generation status response (success)."""
    return {
        "base_resp": {"status_code": 0, "status_msg": "success"},
        "task_id": "mock-task-12345",
        "status": "Success",
        "file_id": "362067136205243",
    }


def get_files_retrieve_response() -> dict[str, Any]:
    """Get file retrieve response with download URL."""
    return {
        "base_resp": {"status_code": 0, "status_msg": "success"},
        "file": {
            "file_id": "362067136205243",
            "download_url": "https://cdn.minimax.io/videos/mock-video.mp4",
        },
    }


# Error responses for testing error handling
def get_auth_error_response() -> dict[str, Any]:
    """Get authentication error response."""
    return {
        "base_resp": {
            "status_code": 1004,
            "status_msg": "login fail: Please carry the API secret key in the 'Authorization' field of the request header",
        }
    }


def get_duplicate_voice_id_error() -> dict[str, Any]:
    """Get duplicate voice_id error response."""
    return {"base_resp": {"status_code": 1001, "status_msg": "voice clone voice id duplicate"}}


def get_video_generation_failure() -> dict[str, Any]:
    """Get video generation failure response."""
    return {
        "base_resp": {"status_code": 0, "status_msg": "success"},
        "task_id": "mock-task-12345",
        "status": "Fail",
        "error_msg": "Content policy violation",
    }


# Helper class for creating mock responses in tests
class MinimaxMockResponses:
    """Helper class for MiniMax mock responses."""

    @staticmethod
    def files_upload(success: bool = True) -> dict[str, Any]:
        """Get file upload response."""
        if success:
            return get_files_upload_response()
        return get_auth_error_response()

    @staticmethod
    def voice_clone(success: bool = True, duplicate: bool = False) -> dict[str, Any]:
        """Get voice clone response."""
        if not success:
            return get_auth_error_response()
        if duplicate:
            return get_duplicate_voice_id_error()
        return get_voice_clone_response()

    @staticmethod
    def t2a_v2(success: bool = True) -> dict[str, Any]:
        """Get text-to-audio response."""
        if success:
            return get_t2a_v2_response()
        return get_auth_error_response()

    @staticmethod
    def video_generation(success: bool = True) -> dict[str, Any]:
        """Get video generation task creation response."""
        if success:
            return get_video_generation_response()
        return get_auth_error_response()

    @staticmethod
    def query_video_generation(status: str = "Success") -> dict[str, Any]:
        """Get video generation status response.

        Args:
            status: "Processing", "Success", or "Fail"
        """
        if status == "Success":
            return get_query_video_generation_success()
        elif status == "Fail":
            return get_video_generation_failure()
        else:  # Processing
            return get_query_video_generation_processing()

    @staticmethod
    def files_retrieve(success: bool = True) -> dict[str, Any]:
        """Get file retrieve response."""
        if success:
            return get_files_retrieve_response()
        return get_auth_error_response()
