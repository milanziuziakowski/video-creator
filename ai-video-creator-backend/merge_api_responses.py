"""
Merge all captured API responses into a unified format for mocking.

This script:
1. Reads all real API response files
2. Merges them into a single comprehensive mock data file
3. Updates the frontend TypeScript mocks with real data

Usage:
    python merge_api_responses.py
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def load_json_safe(file_path: Path) -> Dict[str, Any]:
    """Load JSON file safely, returning empty dict if not found."""
    if not file_path.exists():
        print(f"  ⚠️  File not found: {file_path.name}")
        return {}
    
    with open(file_path, "r") as f:
        return json.load(f)


def merge_responses():
    """Merge all API responses into unified format."""
    fixtures_dir = Path(__file__).parent / "tests" / "fixtures"
    
    print("=" * 80)
    print("Merging API Responses")
    print("=" * 80)
    
    # Load all response files
    print("\n📂 Loading response files...")
    
    minimax_real = load_json_safe(fixtures_dir / "minimax_real_responses.json")
    minimax_video = load_json_safe(fixtures_dir / "minimax_video_responses.json")
    openai_plan = load_json_safe(fixtures_dir / "openai_plan_responses.json")
    
    # Build unified structure
    unified = {
        "generated_at": datetime.now().isoformat(),
        "description": "Real API responses captured for E2E test mocking",
        
        "minimax": {
            "files_upload": {},
            "voice_clone": {},
            "t2a_v2": {},
            "video_generation": {},
            "query_video_generation": {},
            "files_retrieve": {},
        },
        
        "openai": {
            "plan_generation": {},
        },
    }
    
    # Merge MiniMax voice cloning responses
    if minimax_real:
        print("  ✓ Found minimax_real_responses.json (voice cloning)")
        
        if "files_upload" in minimax_real:
            unified["minimax"]["files_upload"] = minimax_real["files_upload"]
        
        if "voice_clone" in minimax_real:
            unified["minimax"]["voice_clone"] = minimax_real["voice_clone"]
        
        if "t2a_v2" in minimax_real:
            unified["minimax"]["t2a_v2"] = minimax_real["t2a_v2"]
    
    # Merge MiniMax video responses
    if minimax_video:
        print("  ✓ Found minimax_video_responses.json (video generation)")
        
        if "video_generation" in minimax_video:
            unified["minimax"]["video_generation"] = minimax_video["video_generation"]
        
        if "query_video_generation" in minimax_video:
            unified["minimax"]["query_video_generation"] = minimax_video["query_video_generation"]
        
        if "files_retrieve" in minimax_video:
            unified["minimax"]["files_retrieve"] = minimax_video["files_retrieve"]
    
    # Merge OpenAI responses
    if openai_plan:
        print("  ✓ Found openai_plan_responses.json")
        
        if "plan_generation" in openai_plan:
            unified["openai"]["plan_generation"] = openai_plan["plan_generation"]
    
    # Save unified file
    output_file = fixtures_dir / "all_api_responses.json"
    with open(output_file, "w") as f:
        json.dump(unified, f, indent=2)
    
    print(f"\n✓ Saved unified responses to: {output_file}")
    
    return unified


def generate_typescript_mocks(unified: Dict[str, Any]):
    """Generate TypeScript mock data from unified responses."""
    
    frontend_fixtures = Path(__file__).parent.parent / "ai-video-creator-frontend" / "e2e" / "fixtures"
    
    print("\n" + "=" * 80)
    print("Generating TypeScript Mocks")
    print("=" * 80)
    
    # Extract data for TypeScript
    minimax = unified.get("minimax", {})
    openai_data = unified.get("openai", {})
    
    # Build mock values
    files_upload = minimax.get("files_upload", {}).get("response", {})
    voice_clone = minimax.get("voice_clone", {}).get("response", {})
    t2a_v2 = minimax.get("t2a_v2", {}).get("response", {})
    video_gen = minimax.get("video_generation", {}).get("response", {})
    video_query = minimax.get("query_video_generation", {})
    files_retrieve = minimax.get("files_retrieve", {}).get("response", {})
    
    plan = openai_data.get("plan_generation", {}).get("response", {}).get("plan", {})
    
    # Create summary for manual update
    summary = {
        "minimax_mocks": {
            "filesUpload": {
                "file_id": files_upload.get("file_id", "NEEDS_REAL_DATA"),
                "status": "success",
            },
            "voiceClone": {
                "voice_id": voice_clone.get("voice_id", "NEEDS_REAL_DATA"),
                "status": "success",
            },
            "textToAudio": {
                "audio_size_bytes": t2a_v2.get("audio_size_bytes", 0),
                "status": "success",
                "voice_id": voice_clone.get("voice_id", "NEEDS_REAL_DATA"),
            },
            "videoGeneration": {
                "task_id": video_gen.get("task_id", "NEEDS_REAL_DATA"),
                "status": "submitted",
            },
            "videoStatusProcessing": {
                "task_id": video_gen.get("task_id", "NEEDS_REAL_DATA"),
                "status": "Processing",
            },
            "videoStatusSuccess": {
                "task_id": video_gen.get("task_id", "NEEDS_REAL_DATA"),
                "status": "Success",
                "file_id": video_query.get("file_id", "NEEDS_REAL_DATA"),
            },
            "fileRetrieve": {
                "file_id": video_query.get("file_id", "NEEDS_REAL_DATA"),
                "download_url": files_retrieve.get("file", {}).get("download_url", "NEEDS_REAL_DATA"),
            },
        },
        "openai_plan": plan if plan else "NEEDS_REAL_DATA",
    }
    
    # Save TypeScript-ready data
    output_file = frontend_fixtures / "real-api-data.json"
    with open(output_file, "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✓ Saved TypeScript-ready data to: {output_file}")
    print("\n📋 Use this data to update minimax-mocks.ts manually")
    
    return summary


def print_status_report(unified: Dict[str, Any]):
    """Print status of what data is captured."""
    
    print("\n" + "=" * 80)
    print("📊 API Response Coverage Report")
    print("=" * 80)
    
    minimax = unified.get("minimax", {})
    openai_data = unified.get("openai", {})
    
    endpoints = [
        ("MiniMax", "files_upload", "POST /v1/files/upload"),
        ("MiniMax", "voice_clone", "POST /v1/voice_clone"),
        ("MiniMax", "t2a_v2", "POST /v1/t2a_v2"),
        ("MiniMax", "video_generation", "POST /v1/video_generation"),
        ("MiniMax", "query_video_generation", "GET /v1/query/video_generation"),
        ("MiniMax", "files_retrieve", "GET /v1/files/retrieve"),
        ("OpenAI", "plan_generation", "POST /v1/chat/completions"),
    ]
    
    print("\n  Endpoint                              Status")
    print("  " + "-" * 50)
    
    for provider, key, endpoint in endpoints:
        if provider == "MiniMax":
            data = minimax.get(key, {})
        else:
            data = openai_data.get(key, {})
        
        has_data = bool(data) and data.get("status") != "error"
        status = "✅ Real data" if has_data else "❌ Missing"
        
        print(f"  {endpoint:<40} {status}")
    
    print("\n")


def main():
    """Run the merge process."""
    print("\n" + "=" * 80)
    print("API RESPONSE MERGER")
    print("=" * 80)
    
    # Merge responses
    unified = merge_responses()
    
    # Generate TypeScript mocks
    summary = generate_typescript_mocks(unified)
    
    # Print status report
    print_status_report(unified)
    
    print("\n📝 Next Steps:")
    print("  1. Run test_minimax_video.py to capture video generation responses")
    print("  2. Run test_openai_plan.py to capture plan generation responses")
    print("  3. Run this script again to merge all responses")
    print("  4. Update minimax-mocks.ts with data from real-api-data.json")


if __name__ == "__main__":
    main()
