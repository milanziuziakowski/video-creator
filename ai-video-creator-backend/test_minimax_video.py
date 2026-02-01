"""
Test script to capture REAL MiniMax video generation API responses.

IMPORTANT: This script makes REAL API calls that cost money.
Run ONCE to capture responses, then use mocks for all future tests.

Prerequisites:
1. Valid MINIMAX_API_KEY in .env
2. test-image.jpg in ../ai-video-creator-frontend/e2e/fixtures/

Usage:
    python test_minimax_video.py
"""

import asyncio
import base64
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure we can import from app
import sys
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings


# Configuration - EDIT THESE BEFORE RUNNING
CONFIG = {
    # Video prompt for test
    "video_prompt": "The man jumps and the video quality is super good. The lighting is glorious",
    
    # Duration: 6 or 10 seconds (6 is cheaper)
    "duration": 6,
    
    # Resolution: 768P or 1080P (768P is cheaper)
    "resolution": "768P",
    
    # Model (required for FL2V)
    "model": "MiniMax-Hailuo-02",
    
    # Poll interval in seconds (MiniMax recommends 10s)
    "poll_interval": 10,
    
    # Max poll attempts (10 minutes max wait)
    "max_poll_attempts": 60,
    
    # Use last-frame image instead of first-frame for FL2V
    "use_last_frame": True,
}


async def load_image_as_base64(image_path: Path) -> str:
    """Load image file and convert to base64 data URL."""
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    
    # Determine MIME type from extension
    ext = image_path.suffix.lower()
    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }
    mime_type = mime_types.get(ext, "image/jpeg")
    
    # Create data URL
    b64_data = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{b64_data}"


async def test_video_generation():
    """
    Test MiniMax video generation workflow and capture real responses.
    
    Workflow:
    1. POST /v1/video_generation - Start task
    2. GET /v1/query/video_generation - Poll until complete
    3. GET /v1/files/retrieve - Get download URL
    """
    import httpx
    
    print("=" * 80)
    print("MiniMax Video Generation Test")
    print("=" * 80)
    
    api_key = settings.MINIMAX_API_KEY
    if not api_key or api_key == "":
        print("ERROR: MINIMAX_API_KEY not configured in .env")
        return None
    
    print(f"\nAPI Key (first 20 chars): {api_key[:20]}...")
    
    # Load test image (last-frame for FL2V)
    image_path = Path(__file__).parent.parent / "ai-video-creator-frontend" / "e2e" / "fixtures" / "last-frame.jpg"
    print(f"\nLoading last-frame image from: {image_path}")
    
    try:
        last_frame_base64 = await load_image_as_base64(image_path)
        print(f"✓ Image loaded, base64 length: {len(last_frame_base64)} chars")
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        print("\nPlease ensure last-frame.jpg exists in:")
        print(f"  {image_path}")
        return None
    
    # API base
    base_url = "https://api.minimax.io/v1"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    results: Dict[str, Any] = {
        "test_timestamp": datetime.now().isoformat(),
        "config": CONFIG,
    }
    
    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=30.0)) as client:
        # Step 1: Start video generation
        print("\n" + "-" * 40)
        print("[STEP 1] Starting video generation task...")
        print("-" * 40)
        
        # FL2V requires last_frame_image (first_frame_image is optional)
        payload = {
            "model": CONFIG["model"],
            "prompt": CONFIG["video_prompt"],
            "last_frame_image": last_frame_base64,
            "duration": CONFIG["duration"],
            "resolution": CONFIG["resolution"],
            "prompt_optimizer": True,
        }
        
        print(f"Prompt: {CONFIG['video_prompt'][:60]}...")
        print(f"Duration: {CONFIG['duration']}s, Resolution: {CONFIG['resolution']}")
        
        try:
            response = await client.post(
                f"{base_url}/video_generation",
                headers=headers,
                json=payload,
            )
            
            response_data = response.json()
            print(f"\nResponse status: {response.status_code}")
            print(f"Response body: {json.dumps(response_data, indent=2)}")
            
            if response.status_code != 200:
                print(f"✗ API error: {response.text}")
                results["video_generation"] = {
                    "status": "error",
                    "http_status": response.status_code,
                    "error": response.text,
                }
                return results
            
            # Check for API-level errors
            base_resp = response_data.get("base_resp", {})
            if base_resp.get("status_code") != 0:
                error_msg = base_resp.get("status_msg", "Unknown error")
                print(f"✗ MiniMax API error: {error_msg}")
                results["video_generation"] = {
                    "status": "error",
                    "api_error": error_msg,
                    "full_response": response_data,
                }
                return results
            
            task_id = response_data.get("task_id")
            print(f"\n✓ Video generation started!")
            print(f"  Task ID: {task_id}")
            
            results["video_generation"] = {
                "endpoint": "POST /v1/video_generation",
                "request": {
                    "model": CONFIG["model"],
                    "prompt": CONFIG["video_prompt"],
                    "last_frame_image": "<base64_image_data>",
                    "duration": CONFIG["duration"],
                    "resolution": CONFIG["resolution"],
                    "prompt_optimizer": True,
                },
                "response": {
                    "task_id": task_id,
                    "base_resp": base_resp,
                },
                "status": "success",
            }
            
        except Exception as e:
            print(f"✗ Request failed: {e}")
            results["video_generation"] = {"status": "error", "error": str(e)}
            return results
        
        # Step 2: Poll for completion
        print("\n" + "-" * 40)
        print("[STEP 2] Polling for video completion...")
        print("-" * 40)
        
        file_id = None
        poll_responses = []
        
        for attempt in range(CONFIG["max_poll_attempts"]):
            print(f"\nPoll attempt {attempt + 1}/{CONFIG['max_poll_attempts']}...")
            
            try:
                response = await client.get(
                    f"{base_url}/query/video_generation",
                    headers=headers,
                    params={"task_id": task_id},
                )
                
                response_data = response.json()
                status = response_data.get("status", "unknown")
                
                # Capture unique status responses
                if not any(r.get("status") == status for r in poll_responses):
                    poll_responses.append({
                        "status": status,
                        "response": response_data,
                        "attempt": attempt + 1,
                    })
                
                print(f"  Status: {status}")
                
                if status == "Success":
                    file_id = response_data.get("file_id")
                    print(f"\n✓ Video generation complete!")
                    print(f"  File ID: {file_id}")
                    
                    results["query_video_generation"] = {
                        "endpoint": "GET /v1/query/video_generation",
                        "request": {"task_id": task_id},
                        "responses": poll_responses,
                        "final_status": "Success",
                        "file_id": file_id,
                    }
                    break
                    
                elif status == "Fail":
                    error = response_data.get("error", "Unknown error")
                    print(f"\n✗ Video generation failed: {error}")
                    
                    results["query_video_generation"] = {
                        "endpoint": "GET /v1/query/video_generation",
                        "request": {"task_id": task_id},
                        "responses": poll_responses,
                        "final_status": "Fail",
                        "error": error,
                    }
                    return results
                
                # Still processing, wait before next poll
                print(f"  Waiting {CONFIG['poll_interval']}s...")
                await asyncio.sleep(CONFIG["poll_interval"])
                
            except Exception as e:
                print(f"✗ Poll request failed: {e}")
                poll_responses.append({"error": str(e), "attempt": attempt + 1})
        
        else:
            print(f"\n✗ Timeout after {CONFIG['max_poll_attempts']} attempts")
            results["query_video_generation"] = {
                "status": "timeout",
                "responses": poll_responses,
            }
            return results
        
        # Step 3: Get download URL
        if file_id:
            print("\n" + "-" * 40)
            print("[STEP 3] Retrieving download URL...")
            print("-" * 40)
            
            try:
                response = await client.get(
                    f"{base_url}/files/retrieve",
                    headers=headers,
                    params={"file_id": file_id},
                )
                
                response_data = response.json()
                print(f"\nResponse: {json.dumps(response_data, indent=2)}")
                
                download_url = response_data.get("file", {}).get("download_url")
                
                if download_url:
                    print(f"\n✓ Download URL retrieved!")
                    print(f"  URL: {download_url[:80]}...")
                    
                    results["files_retrieve"] = {
                        "endpoint": "GET /v1/files/retrieve",
                        "request": {"file_id": file_id},
                        "response": {
                            "file": {
                                "file_id": file_id,
                                "download_url": download_url,
                            }
                        },
                        "status": "success",
                    }
                else:
                    print(f"✗ No download URL in response")
                    results["files_retrieve"] = {
                        "status": "error",
                        "response": response_data,
                    }
                    
            except Exception as e:
                print(f"✗ Retrieve request failed: {e}")
                results["files_retrieve"] = {"status": "error", "error": str(e)}
    
    return results


async def main():
    """Run the test and save results."""
    print("\n" + "=" * 80)
    print("MINIMAX VIDEO GENERATION API TEST")
    print("=" * 80)
    print("\n⚠️  WARNING: This script makes REAL API calls!")
    print("   Estimated cost: ~$0.20-0.50 for a 6s video")
    print("\n")
    
    # Ask for confirmation
    confirm = input("Continue? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Aborted.")
        return
    
    # Run the test
    results = await test_video_generation()
    
    if results:
        # Save results
        output_file = Path(__file__).parent / "tests" / "fixtures" / "minimax_video_responses.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        
        print("\n" + "=" * 80)
        print(f"✓ Results saved to: {output_file}")
        print("=" * 80)
        
        # Print summary
        print("\n📊 Summary:")
        if results.get("video_generation", {}).get("status") == "success":
            print(f"  ✓ Task ID: {results['video_generation']['response']['task_id']}")
        if results.get("query_video_generation", {}).get("final_status") == "Success":
            print(f"  ✓ File ID: {results['query_video_generation']['file_id']}")
        if results.get("files_retrieve", {}).get("status") == "success":
            print(f"  ✓ Download URL available")
    else:
        print("\n✗ Test failed - no results to save")


if __name__ == "__main__":
    asyncio.run(main())
