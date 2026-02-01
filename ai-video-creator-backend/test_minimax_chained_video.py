"""
Test script to capture REAL MiniMax video generation with chained segments.

This tests the REAL workflow:
1. Segment 1: First frame + Last frame (FL2V)
2. Segment 2: Last frame from Segment 1 video as first frame
3. Segment 3: Last frame from Segment 2 video as first frame

IMPORTANT: This script makes REAL API calls that cost money (~$0.60-1.50 for 3 videos)
Run ONCE to capture responses, then use mocks for all future tests.

Prerequisites:
1. Valid MINIMAX_API_KEY in .env
2. first-frame.jpg and last-frame.jpg in frontend fixtures
3. FFmpeg installed and in PATH

Usage:
    python test_minimax_chained_video.py
"""

import asyncio
import base64
import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

# Ensure we can import from app
import sys
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings


# Configuration
CONFIG = {
    # Video prompts for each segment (from OpenAI plan)
    "prompts": [
        "The scene opens with a wide shot of a solitary man standing on a rugged mountain peak, surrounded by vast, snow-capped ranges. The sky is a brilliant blue with a few wispy clouds. [Zoom in] slowly towards the man as the wind gently rustles his hair and clothes, creating a sense of solitude and determination.",
        "Cut to a medium shot of the man spreading his arms wide, as if preparing to take flight. [Tilt down] to show his feet firmly planted on the rocky ground, emphasizing the contrast between his dreams and reality. The light is warm, casting long shadows.",
        "Transition to a close-up of the man's face as he lowers his arms and smiles softly. [Pull out] to reveal the surrounding landscape, capturing the peaceful and accepting atmosphere. The golden light of the setting sun bathes the scene, adding warmth and tranquility.",
    ],
    
    # Duration: 6 or 10 seconds
    "duration": 6,
    
    # Resolution: 768P or 1080P
    "resolution": "768P",
    
    # Model
    "model": "MiniMax-Hailuo-02",
    
    # Poll settings
    "poll_interval": 10,
    "max_poll_attempts": 60,
}

# MiniMax API settings
MINIMAX_API_BASE = "https://api.minimax.io/v1"


async def load_image_as_base64(image_path: Path) -> str:
    """Load image file and convert to base64 data URL."""
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    
    ext = image_path.suffix.lower()
    mime_types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    mime_type = mime_types.get(ext, "image/jpeg")
    
    b64_data = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{b64_data}"


def extract_last_frame_ffmpeg(video_path: Path, output_path: Path) -> bool:
    """Extract the last frame from a video using FFmpeg."""
    print(f"  Extracting last frame from: {video_path.name}")
    
    try:
        # First, get video duration
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path)
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        duration = float(result.stdout.strip())
        print(f"  Video duration: {duration:.2f}s")
        
        # Extract frame at duration - 0.1s (to ensure we get a valid frame)
        seek_time = max(0, duration - 0.1)
        
        extract_cmd = [
            "ffmpeg", "-y",
            "-ss", str(seek_time),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_path)
        ]
        
        result = subprocess.run(extract_cmd, capture_output=True, text=True)
        
        if output_path.exists() and output_path.stat().st_size > 0:
            print(f"  ✓ Last frame extracted: {output_path.name} ({output_path.stat().st_size} bytes)")
            return True
        else:
            print(f"  ✗ Failed to extract frame: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ✗ FFmpeg error: {e}")
        return False


async def download_video(url: str, output_path: Path) -> bool:
    """Download video from URL."""
    print(f"  Downloading video to: {output_path.name}")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(url)
            
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                print(f"  ✓ Downloaded: {output_path.stat().st_size} bytes")
                return True
            else:
                print(f"  ✗ Download failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"  ✗ Download error: {e}")
        return False


async def generate_video(
    client: httpx.AsyncClient,
    headers: dict,
    prompt: str,
    first_frame: Optional[str] = None,
    last_frame: Optional[str] = None,
) -> Dict[str, Any]:
    """Start video generation and return task info."""
    
    payload = {
        "model": CONFIG["model"],
        "prompt": prompt,
        "duration": CONFIG["duration"],
        "resolution": CONFIG["resolution"],
        "prompt_optimizer": True,
    }
    
    if first_frame:
        payload["first_frame_image"] = first_frame
    if last_frame:
        payload["last_frame_image"] = last_frame
    
    response = await client.post(
        f"{MINIMAX_API_BASE}/video_generation",
        headers=headers,
        json=payload,
    )
    
    return response.json()


async def poll_video_status(
    client: httpx.AsyncClient,
    headers: dict,
    task_id: str,
) -> Dict[str, Any]:
    """Poll for video completion."""
    
    statuses_captured = []
    
    for attempt in range(CONFIG["max_poll_attempts"]):
        response = await client.get(
            f"{MINIMAX_API_BASE}/query/video_generation",
            headers=headers,
            params={"task_id": task_id},
        )
        
        data = response.json()
        status = data.get("status", "unknown")
        
        # Capture unique statuses
        if not any(s.get("status") == status for s in statuses_captured):
            statuses_captured.append({"status": status, "response": data, "attempt": attempt + 1})
        
        print(f"    Poll {attempt + 1}: {status}")
        
        if status == "Success":
            return {
                "success": True,
                "file_id": data.get("file_id"),
                "video_width": data.get("video_width"),
                "video_height": data.get("video_height"),
                "statuses": statuses_captured,
            }
        elif status == "Fail":
            return {"success": False, "error": data.get("error"), "statuses": statuses_captured}
        
        await asyncio.sleep(CONFIG["poll_interval"])
    
    return {"success": False, "error": "Timeout", "statuses": statuses_captured}


async def retrieve_download_url(
    client: httpx.AsyncClient,
    headers: dict,
    file_id: str,
) -> Optional[str]:
    """Get download URL for video file."""
    
    response = await client.get(
        f"{MINIMAX_API_BASE}/files/retrieve",
        headers=headers,
        params={"file_id": file_id},
    )
    
    data = response.json()
    return data.get("file", {}).get("download_url")


async def test_chained_video_generation():
    """Test chained video generation workflow."""
    
    print("=" * 80)
    print("MiniMax Chained Video Generation Test")
    print("=" * 80)
    
    api_key = settings.MINIMAX_API_KEY
    if not api_key:
        print("ERROR: MINIMAX_API_KEY not configured")
        return None
    
    print(f"\nAPI Key (first 20 chars): {api_key[:20]}...")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    # Load initial frames
    fixtures_dir = Path(__file__).parent.parent / "ai-video-creator-frontend" / "e2e" / "fixtures"
    first_frame_path = fixtures_dir / "first-frame.jpg"
    last_frame_path = fixtures_dir / "last-frame.jpg"
    
    print(f"\nLoading initial frames...")
    print(f"  First frame: {first_frame_path}")
    print(f"  Last frame: {last_frame_path}")
    
    try:
        initial_first_frame = await load_image_as_base64(first_frame_path)
        initial_last_frame = await load_image_as_base64(last_frame_path)
        print(f"  ✓ Frames loaded")
    except FileNotFoundError as e:
        print(f"  ✗ Error: {e}")
        return None
    
    # Create temp directory for downloaded videos and extracted frames
    temp_dir = Path(tempfile.mkdtemp(prefix="minimax_test_"))
    print(f"\nTemp directory: {temp_dir}")
    
    # Results structure
    results = {
        "test_timestamp": datetime.now().isoformat(),
        "config": CONFIG,
        "segments": [],
    }
    
    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=30.0)) as client:
        
        current_first_frame = initial_first_frame
        
        for seg_index in range(3):
            print("\n" + "=" * 80)
            print(f"SEGMENT {seg_index + 1} / 3")
            print("=" * 80)
            
            segment_result = {
                "segment_index": seg_index,
                "prompt": CONFIG["prompts"][seg_index][:60] + "...",
            }
            
            # Determine frames for this segment
            if seg_index == 0:
                # First segment: use both first and last frames (FL2V)
                print(f"\n[Segment 1] Using FIRST + LAST frames (FL2V)")
                first_frame = initial_first_frame
                last_frame = initial_last_frame
                segment_result["frame_source"] = "initial_first_frame + initial_last_frame"
            else:
                # Subsequent segments: use extracted last frame as first frame only
                print(f"\n[Segment {seg_index + 1}] Using extracted last frame as FIRST frame only")
                first_frame = current_first_frame
                last_frame = None
                segment_result["frame_source"] = f"last_frame_from_segment_{seg_index}"
            
            # Step 1: Start video generation
            print(f"\n[STEP 1] Starting video generation...")
            print(f"  Prompt: {CONFIG['prompts'][seg_index][:60]}...")
            print(f"  Has first_frame: {first_frame is not None}")
            print(f"  Has last_frame: {last_frame is not None}")
            
            try:
                gen_response = await generate_video(
                    client, headers,
                    CONFIG["prompts"][seg_index],
                    first_frame=first_frame,
                    last_frame=last_frame,
                )
                
                if gen_response.get("base_resp", {}).get("status_code") != 0:
                    error_msg = gen_response.get("base_resp", {}).get("status_msg", "Unknown error")
                    print(f"  ✗ API error: {error_msg}")
                    segment_result["error"] = error_msg
                    results["segments"].append(segment_result)
                    continue
                
                task_id = gen_response.get("task_id")
                print(f"  ✓ Task started: {task_id}")
                
                segment_result["video_generation"] = {
                    "request": {
                        "model": CONFIG["model"],
                        "prompt": CONFIG["prompts"][seg_index],
                        "first_frame_image": "<base64_data>" if first_frame else None,
                        "last_frame_image": "<base64_data>" if last_frame else None,
                        "duration": CONFIG["duration"],
                        "resolution": CONFIG["resolution"],
                    },
                    "response": {
                        "task_id": task_id,
                        "base_resp": gen_response.get("base_resp"),
                    },
                }
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                segment_result["error"] = str(e)
                results["segments"].append(segment_result)
                continue
            
            # Step 2: Poll for completion
            print(f"\n[STEP 2] Polling for completion...")
            poll_result = await poll_video_status(client, headers, task_id)
            
            if not poll_result["success"]:
                print(f"  ✗ Generation failed: {poll_result.get('error')}")
                segment_result["error"] = poll_result.get("error")
                segment_result["poll_statuses"] = poll_result.get("statuses", [])
                results["segments"].append(segment_result)
                continue
            
            file_id = poll_result["file_id"]
            print(f"  ✓ Complete! File ID: {file_id}")
            
            segment_result["query_video_generation"] = {
                "statuses": poll_result["statuses"],
                "final_file_id": file_id,
                "video_width": poll_result.get("video_width"),
                "video_height": poll_result.get("video_height"),
            }
            
            # Step 3: Get download URL
            print(f"\n[STEP 3] Retrieving download URL...")
            download_url = await retrieve_download_url(client, headers, file_id)
            
            if not download_url:
                print(f"  ✗ Failed to get download URL")
                segment_result["error"] = "No download URL"
                results["segments"].append(segment_result)
                continue
            
            print(f"  ✓ URL: {download_url[:80]}...")
            
            segment_result["files_retrieve"] = {
                "file_id": file_id,
                "download_url": download_url,
            }
            
            # Step 4: Download video and extract last frame for next segment
            if seg_index < 2:  # Not needed for last segment
                print(f"\n[STEP 4] Downloading video and extracting last frame...")
                
                video_path = temp_dir / f"segment_{seg_index + 1}.mp4"
                frame_path = temp_dir / f"segment_{seg_index + 1}_last_frame.jpg"
                
                # Download
                download_ok = await download_video(download_url, video_path)
                
                if download_ok:
                    # Extract last frame
                    extract_ok = extract_last_frame_ffmpeg(video_path, frame_path)
                    
                    if extract_ok:
                        # Load as base64 for next segment
                        current_first_frame = await load_image_as_base64(frame_path)
                        print(f"  ✓ Frame ready for next segment")
                        
                        segment_result["extracted_frame"] = {
                            "path": str(frame_path),
                            "size_bytes": frame_path.stat().st_size,
                        }
                    else:
                        print(f"  ✗ Frame extraction failed - stopping chain")
                        results["segments"].append(segment_result)
                        break
                else:
                    print(f"  ✗ Download failed - stopping chain")
                    results["segments"].append(segment_result)
                    break
            
            results["segments"].append(segment_result)
            print(f"\n✓ Segment {seg_index + 1} complete!")
    
    # Save extracted frames to fixtures for future use
    print("\n" + "=" * 80)
    print("Saving extracted frames to fixtures...")
    print("=" * 80)
    
    for seg_index in range(2):
        src_frame = temp_dir / f"segment_{seg_index + 1}_last_frame.jpg"
        if src_frame.exists():
            dst_frame = fixtures_dir / f"segment-{seg_index + 1}-last-frame.jpg"
            import shutil
            shutil.copy(src_frame, dst_frame)
            print(f"  ✓ Saved: {dst_frame.name}")
    
    return results


async def main():
    """Run the test and save results."""
    
    print("\n" + "=" * 80)
    print("MINIMAX CHAINED VIDEO GENERATION TEST")
    print("=" * 80)
    print("\n⚠️  WARNING: This script makes REAL API calls!")
    print("   Estimated cost: ~$0.60-1.50 for 3 videos (6s each)")
    print("   Estimated time: ~3-5 minutes")
    print("\n")
    
    # Ask for confirmation
    confirm = input("Continue? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Aborted.")
        return
    
    # Run the test
    results = await test_chained_video_generation()
    
    if results:
        # Save results
        output_file = Path(__file__).parent / "tests" / "fixtures" / "minimax_chained_video_responses.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        
        print("\n" + "=" * 80)
        print(f"✓ Results saved to: {output_file}")
        print("=" * 80)
        
        # Print summary
        print("\n📊 Summary:")
        for seg in results.get("segments", []):
            idx = seg.get("segment_index", "?")
            if "error" in seg:
                print(f"  Segment {idx + 1}: ✗ {seg['error']}")
            else:
                file_id = seg.get("query_video_generation", {}).get("final_file_id", "N/A")
                print(f"  Segment {idx + 1}: ✓ file_id={file_id}")
    else:
        print("\n✗ Test failed - no results to save")


if __name__ == "__main__":
    asyncio.run(main())
