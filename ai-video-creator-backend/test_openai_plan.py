"""
Test script to capture REAL OpenAI API responses for video plan generation.

IMPORTANT: This script makes REAL API calls that cost money.
Run ONCE to capture responses, then use mocks for all future tests.

Prerequisites:
1. Valid OPENAI_API_KEY in .env

Usage:
    python test_openai_plan.py
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Ensure we can import from app
import sys
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings


# Configuration - EDIT THESE BEFORE RUNNING
CONFIG = {
    # Story prompt for test (same as frontend mock would use)
    "story_prompt": "The man travel over mountains and tries to fly but he can't. Anyway he smiles and tries to be happy.",
    
    # Number of segments (3 for 18s total at 6s each)
    "segment_count": 3,
    
    # Duration per segment in seconds
    "segment_duration": 6,
    
    # Model to use
    "model": "gpt-4o",
    
    # Temperature for creativity
    "temperature": 0.7,
}


# System prompt (same as in plan_generator.py)
SYSTEM_PROMPT = """You are an expert video story planner specializing in creating cohesive, 
visually compelling narratives for short-form video content.

IMPORTANT: Generate all output in POLISH language.

Your task is to break down a user's story concept into video segments with:
1. Detailed video prompts (scene composition, lighting, camera movement, atmosphere)
2. Voice-over narration text
3. End-frame descriptions for seamless transitions

Guidelines for video prompts:
- Each video prompt should be 2-3 sentences with specific visual details
- Include emotional tone, atmosphere, and camera movement suggestions
- Use MiniMax camera commands when appropriate: [Zoom in], [Zoom out], [Pan left], [Pan right], 
  [Tilt up], [Tilt down], [Push in], [Pull out], [Tracking shot], [Static shot]
- Ensure each segment's end naturally leads to the next segment's beginning

Guidelines for narration:
- Keep narration natural and conversational
- Match pacing to segment duration (roughly 2-3 sentences per 6 seconds)
- Complement visuals without being redundant
- Create a narrative arc across all segments

Guidelines for end-frame prompts:
- Describe the exact visual state at the end of the segment
- This becomes the starting point for the next segment
- Ensure smooth transitions between segments

Maintain consistent visual style, characters, and atmosphere throughout all segments.

All text must be in Polish language (video prompts, narration, and end-frame descriptions)."""


async def test_plan_generation():
    """
    Test OpenAI structured output plan generation and capture real response.
    """
    from openai import AsyncOpenAI
    from pydantic import BaseModel, Field
    
    print("=" * 80)
    print("OpenAI Video Plan Generation Test")
    print("=" * 80)
    
    api_key = settings.OPENAI_API_KEY
    if not api_key or api_key == "":
        print("ERROR: OPENAI_API_KEY not configured in .env")
        return None
    
    print(f"\nAPI Key (first 20 chars): {api_key[:20]}...")
    
    # Define Pydantic models for structured output
    class SegmentPrompt(BaseModel):
        """Single segment prompt schema."""
        segment_index: int = Field(..., description="0-indexed segment number")
        video_prompt: str = Field(..., description="Detailed visual description for video generation")
        narration_text: str = Field(..., description="Voice-over narration text")
        end_frame_prompt: str = Field(..., description="Description of the final frame")

    class VideoStoryPlan(BaseModel):
        """Complete video plan schema."""
        title: str = Field(..., description="Video title")
        segments: List[SegmentPrompt] = Field(..., description="List of segment prompts")
        continuity_notes: str = Field(..., description="Notes about visual continuity between segments")
    
    client = AsyncOpenAI(api_key=api_key)
    
    user_message = f"""Create a video story plan for:

Story concept: {CONFIG['story_prompt']}

Requirements:
- {CONFIG['segment_count']} segments of {CONFIG['segment_duration']} seconds each
- Total duration: {CONFIG['segment_count'] * CONFIG['segment_duration']} seconds

Generate cinematic prompts with smooth visual transitions between segments.
Each video_prompt should include specific visual details and can include camera commands.
Each narration_text should match the segment duration (~{CONFIG['segment_duration']} seconds of speech).
Each end_frame_prompt should describe where the segment visually ends for seamless transition."""

    print(f"\nStory prompt: {CONFIG['story_prompt']}")
    print(f"Segments: {CONFIG['segment_count']} × {CONFIG['segment_duration']}s")
    
    results: Dict[str, Any] = {
        "test_timestamp": datetime.now().isoformat(),
        "config": CONFIG,
    }
    
    print("\n" + "-" * 40)
    print("Calling OpenAI API...")
    print("-" * 40)
    
    try:
        completion = await client.beta.chat.completions.parse(
            model=CONFIG["model"],
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            response_format=VideoStoryPlan,
            temperature=CONFIG["temperature"],
        )
        
        plan = completion.choices[0].message.parsed
        
        if plan is None:
            print("✗ No response from API")
            results["plan_generation"] = {"status": "error", "error": "No response"}
            return results
        
        print(f"\n✓ Plan generated successfully!")
        print(f"  Title: {plan.title}")
        print(f"  Segments: {len(plan.segments)}")
        
        # Convert to dict for JSON serialization
        plan_dict = {
            "title": plan.title,
            "segments": [
                {
                    "segment_index": seg.segment_index,
                    "video_prompt": seg.video_prompt,
                    "narration_text": seg.narration_text,
                    "end_frame_prompt": seg.end_frame_prompt,
                }
                for seg in plan.segments
            ],
            "continuity_notes": plan.continuity_notes,
        }
        
        # Print segments summary
        for seg in plan.segments:
            print(f"\n  Segment {seg.segment_index}:")
            print(f"    Video: {seg.video_prompt[:60]}...")
            print(f"    Narration: {seg.narration_text[:50]}...")
        
        # Capture usage info
        usage = completion.usage
        usage_dict = {
            "prompt_tokens": usage.prompt_tokens if usage else 0,
            "completion_tokens": usage.completion_tokens if usage else 0,
            "total_tokens": usage.total_tokens if usage else 0,
        }
        
        print(f"\n  Token usage: {usage_dict['total_tokens']} total")
        
        results["plan_generation"] = {
            "endpoint": "POST /v1/chat/completions (structured output)",
            "request": {
                "model": CONFIG["model"],
                "messages": [
                    {"role": "system", "content": "<system_prompt>"},
                    {"role": "user", "content": user_message},
                ],
                "response_format": "VideoStoryPlan",
                "temperature": CONFIG["temperature"],
            },
            "response": {
                "plan": plan_dict,
                "usage": usage_dict,
            },
            "status": "success",
        }
        
    except Exception as e:
        print(f"✗ API call failed: {e}")
        results["plan_generation"] = {"status": "error", "error": str(e)}
    
    return results


async def main():
    """Run the test and save results."""
    print("\n" + "=" * 80)
    print("OPENAI VIDEO PLAN GENERATION API TEST")
    print("=" * 80)
    print("\n⚠️  WARNING: This script makes REAL API calls!")
    print("   Estimated cost: ~$0.01-0.05 for a plan generation")
    print("\n")
    
    # Ask for confirmation
    confirm = input("Continue? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Aborted.")
        return
    
    # Run the test
    results = await test_plan_generation()
    
    if results:
        # Save results
        output_file = Path(__file__).parent / "tests" / "fixtures" / "openai_plan_responses.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        
        print("\n" + "=" * 80)
        print(f"✓ Results saved to: {output_file}")
        print("=" * 80)
        
        # Print full response for inspection
        if results.get("plan_generation", {}).get("status") == "success":
            print("\n📋 Full Plan:")
            plan = results["plan_generation"]["response"]["plan"]
            print(json.dumps(plan, indent=2))
    else:
        print("\n✗ Test failed - no results to save")


if __name__ == "__main__":
    asyncio.run(main())
