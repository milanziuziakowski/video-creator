"""AI-powered prompt generation using OpenAI structured outputs.

This module uses OpenAI's structured outputs feature to generate
intelligent, story-driven prompts for video segments with continuity.
"""

import logging
from typing import List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SegmentPrompt(BaseModel):
    """Single segment prompt with video, narration, and end-frame descriptions."""
    
    segment_index: int = Field(..., description="0-indexed segment number")
    video_prompt: str = Field(..., description="Visual description for FL2V video generation")
    narration_text: str = Field(..., description="Voice narration text for this segment")
    end_frame_prompt: str = Field(..., description="Description of final frame for transition")
    
    class Config:
        json_schema_extra = {
            "example": {
                "segment_index": 0,
                "video_prompt": "A sunrise over calm ocean waters, warm orange and pink hues filling the sky",
                "narration_text": "As the sun rises over the peaceful ocean, a new day begins",
                "end_frame_prompt": "The sun fully visible above the horizon, bright morning light"
            }
        }


class VideoStoryPlan(BaseModel):
    """Complete story plan with all segment prompts."""
    
    title: str = Field(..., description="Video title derived from story")
    segments: List[SegmentPrompt] = Field(..., description="List of segment prompts")
    continuity_notes: str = Field(..., description="Notes about visual/narrative continuity")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Ocean Sunrise Journey",
                "segments": [],
                "continuity_notes": "Maintains warm color palette throughout, progressive brightening"
            }
        }


async def generate_story_plan(
    story_prompt: str,
    segment_count: int,
    segment_len_sec: int,
    openai_client,
    model: str = "gpt-4o",
    temperature: float = 0.7,
) -> VideoStoryPlan:
    """Generate intelligent segment prompts using OpenAI structured outputs.
    
    Args:
        story_prompt: User's high-level story concept
        segment_count: Number of segments to generate
        segment_len_sec: Duration of each segment (6 or 10 seconds)
        openai_client: Initialized OpenAI client
        model: OpenAI model to use (default: gpt-4o for structured outputs)
        temperature: Creativity level (0-1)
        
    Returns:
        VideoStoryPlan with all segment prompts generated
        
    Raises:
        Exception: If OpenAI API call fails
        
    Note:
        Uses OpenAI's structured outputs feature for reliable JSON parsing.
        Requires OpenAI API key in environment or client configuration.
        
    Best Practices:
        - Uses Pydantic models for type safety
        - Implements comprehensive system instructions
        - Ensures continuity between segments
        - Provides specific guidance for FL2V video generation
    """
    logger.info(f"Generating story plan: {segment_count} segments of {segment_len_sec}s")
    
    # Construct comprehensive system prompt
    system_prompt = f"""You are an expert video story planner specializing in creating cohesive, 
visually compelling narratives for short-form video content.

Your task is to break down a user's story concept into {segment_count} segments of {segment_len_sec} seconds each.

For each segment, provide:
1. video_prompt: Detailed visual description for FL2V video generation
   - Be specific about scene composition, lighting, movement, atmosphere
   - Ensure visual continuity with previous segment
   - Include camera angles, colors, and emotional tone
   
2. narration_text: Voice-over narration that complements the visuals
   - Keep it natural and conversational
   - Match pacing to {segment_len_sec} seconds
   - Ensure narrative flow between segments
   
3. end_frame_prompt: Precise description of the final frame
   - This becomes the first frame of the next segment
   - Ensures smooth transitions
   - Be very specific about composition and elements

Important guidelines:
- Maintain visual and narrative continuity throughout
- Each segment should feel connected to the previous one
- End frames should naturally lead into next segment's opening
- Keep tone consistent with the overall story theme
- Balance visual interest across all segments
- Ensure the story has a clear beginning, middle, and end arc

Total video duration: {segment_count * segment_len_sec} seconds"""

    user_prompt = f"""Create a video story plan based on this concept:

"{story_prompt}"

Break this into exactly {segment_count} segments. Ensure smooth transitions and compelling storytelling."""

    try:
        # Use OpenAI's structured outputs (beta feature)
        # This ensures reliable JSON parsing with Pydantic validation
        logger.debug("Calling OpenAI API with structured outputs")
        
        completion = await openai_client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=VideoStoryPlan,
            temperature=temperature,
        )
        
        # Extract parsed response
        story_plan = completion.choices[0].message.parsed
        
        logger.info(f"✓ Story plan generated: {story_plan.title}")
        logger.debug(f"Continuity notes: {story_plan.continuity_notes}")
        
        # Validate segment count matches
        if len(story_plan.segments) != segment_count:
            logger.warning(
                f"Generated {len(story_plan.segments)} segments, expected {segment_count}"
            )
        
        return story_plan
        
    except Exception as e:
        logger.error(f"Failed to generate story plan: {e}", exc_info=True)
        raise


async def generate_story_plan_fallback(
    story_prompt: str,
    segment_count: int,
    segment_len_sec: int,
    openai_client,
    model: str = "gpt-4o",
) -> VideoStoryPlan:
    """Fallback method using standard completion API (without structured outputs).
    
    Use this if structured outputs are not available or fail.
    """
    logger.info("Using fallback story generation method")
    
    system_prompt = f"""Generate a JSON response for a video story with {segment_count} segments.
Each segment should have: segment_index, video_prompt, narration_text, end_frame_prompt."""
    
    try:
        completion = await openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Story: {story_prompt}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        
        # Parse JSON response
        import json
        response_data = json.loads(completion.choices[0].message.content)
        
        # Validate and create VideoStoryPlan
        story_plan = VideoStoryPlan.model_validate(response_data)
        
        logger.info(f"✓ Fallback story plan generated: {story_plan.title}")
        return story_plan
        
    except Exception as e:
        logger.error(f"Fallback generation failed: {e}", exc_info=True)
        raise


def create_default_prompts(
    story_prompt: str,
    segment_count: int,
) -> VideoStoryPlan:
    """Create basic placeholder prompts when AI generation is not available.
    
    This provides a fallback when OpenAI API is unavailable or fails.
    """
    logger.warning("Using default placeholder prompts (AI generation unavailable)")
    
    segments = []
    for i in range(segment_count):
        segment = SegmentPrompt(
            segment_index=i,
            video_prompt=f"Scene {i+1} of the story: {story_prompt}",
            narration_text=f"This is segment {i+1} of our story",
            end_frame_prompt=f"Transition to segment {i+2}" if i < segment_count - 1 else "Final scene",
        )
        segments.append(segment)
    
    return VideoStoryPlan(
        title=story_prompt[:50],
        segments=segments,
        continuity_notes="Default prompts - AI generation was not available",
    )
