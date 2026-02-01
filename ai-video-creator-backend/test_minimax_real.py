"""
Test script to make real MiniMax API calls and capture responses.
Run this ONCE to verify authentication and capture real API responses for mocking.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from app.integrations.minimax_client import MinimaxClient
from app.config import settings


async def test_real_api_calls():
    """Make real API calls and save responses."""
    print("=" * 80)
    print("Testing MiniMax API with real credentials")
    print("=" * 80)
    print(f"\nOPENAI_API_KEY (first 20 chars): {settings.OPENAI_API_KEY[:20]}...")
    print(f"MINIMAX_API_KEY (first 20 chars): {settings.MINIMAX_API_KEY[:20]}...")
    print(f"MINIMAX_API_KEY starts with: {settings.MINIMAX_API_KEY[:10]}")
    
    # Create client
    client = MinimaxClient(api_key=settings.MINIMAX_API_KEY)
    
    # Test 1: Upload a file
    print("\n[TEST 1] Uploading test audio file...")
    try:
        # Load the actual test audio file from frontend fixtures
        audio_file_path = Path(__file__).parent.parent / "ai-video-creator-frontend" / "e2e" / "fixtures" / "test-audio.mp3"
        print(f"Loading audio file from: {audio_file_path}")
        
        if not audio_file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        with open(audio_file_path, "rb") as f:
            test_audio = f.read()
        
        print(f"Loaded audio file, size: {len(test_audio)} bytes")
        
        file_id = await client.upload_file(
            file_bytes=test_audio,
            filename="test_sample.mp3",
            purpose="voice_clone"
        )
        print(f"✓ Upload successful! File ID: {file_id}")
        
        # Save response
        upload_response = {"file_id": file_id, "status": "success"}
        
        # Test 2: Clone voice
        print("\n[TEST 2] Cloning voice...")
        try:
            # Use unique voice ID with timestamp to avoid duplicates
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            voice_id = f"test-voice-{timestamp}"
            result_voice_id = await client.voice_clone(
                file_id=file_id,
                voice_id=voice_id,
            )
            print(f"✓ Voice cloning successful! Voice ID: {result_voice_id}")
            
            # Save response
            voice_clone_response = {
                "voice_id": result_voice_id,
                "status": "success",
                "original_file_id": file_id
            }
            
            # Test 3: Text to audio
            print("\n[TEST 3] Generating audio with cloned voice...")
            try:
                audio_bytes = await client.text_to_audio(
                    text="This is a test narration.",
                    voice_id=voice_id,
                )
                print(f"✓ Audio generation successful! Size: {len(audio_bytes)} bytes")
                
                # Save response
                tts_response = {
                    "audio_size_bytes": len(audio_bytes),
                    "status": "success",
                    "voice_id": voice_id
                }
                
            except Exception as e:
                print(f"✗ Audio generation failed: {e}")
                tts_response = {"error": str(e), "status": "failed"}
                
        except Exception as e:
            print(f"✗ Voice cloning failed: {e}")
            voice_clone_response = {"error": str(e), "status": "failed"}
            tts_response = {"error": "Skipped due to voice clone failure", "status": "skipped"}
            
    except Exception as e:
        print(f"✗ Upload failed: {e}")
        upload_response = {"error": str(e), "status": "failed"}
        voice_clone_response = {"error": "Skipped due to upload failure", "status": "skipped"}
        tts_response = {"error": "Skipped due to upload failure", "status": "skipped"}
    
    # Save all responses to a file
    all_responses = {
        "upload": upload_response,
        "voice_clone": voice_clone_response,
        "text_to_audio": tts_response,
    }
    
    output_file = Path(__file__).parent / "tests" / "fixtures" / "minimax_real_responses.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w") as f:
        json.dump(all_responses, f, indent=2)
    
    print("\n" + "=" * 80)
    print(f"✓ All responses saved to: {output_file}")
    print("=" * 80)
    print("\nYou can now use these responses for mocking in tests!")
    print(f"\nResponse summary:")
    print(json.dumps(all_responses, indent=2))


if __name__ == "__main__":
    asyncio.run(test_real_api_calls())
