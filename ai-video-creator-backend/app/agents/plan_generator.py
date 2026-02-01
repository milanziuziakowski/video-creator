"""Video plan generator using OpenAI Structured Outputs."""

import logging

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger(__name__)


class SegmentPrompt(BaseModel):
    """Single segment prompt schema."""

    segment_index: int = Field(..., description="0-indexed segment number")
    video_prompt: str = Field(..., description="Detailed visual description for video generation")
    narration_text: str = Field(..., description="Voice-over narration text")
    end_frame_prompt: str = Field(..., description="Description of the final frame")


class VideoStoryPlan(BaseModel):
    """Complete video plan schema."""

    title: str = Field(..., description="Video title")
    segments: list[SegmentPrompt] = Field(..., description="List of segment prompts")
    continuity_notes: str = Field(..., description="Notes about visual continuity between segments")


class PlanGeneratorAgent:
    """Wrapper agent for generating video plans.

    Exists to provide a class interface for tests/mocking while delegating
    to the structured-output generator.
    """

    async def generate_plan(
        self,
        story_prompt: str,
        segment_count: int,
        segment_duration: int,
    ) -> VideoStoryPlan:
        """Generate a video plan.

        Args:
            story_prompt: User story concept
            segment_count: Number of segments
            segment_duration: Duration per segment in seconds

        Returns:
            VideoStoryPlan
        """
        return await generate_video_plan(
            story_prompt=story_prompt,
            segment_count=segment_count,
            segment_duration=segment_duration,
        )


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


async def generate_video_plan(
    story_prompt: str,
    segment_count: int,
    segment_duration: int,
) -> VideoStoryPlan:
    """Generate video plan using OpenAI structured outputs.

    Args:
        story_prompt: User's story concept
        segment_count: Number of segments to create
        segment_duration: Duration of each segment in seconds

    Returns:
        VideoStoryPlan with all segment prompts
    """
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    user_message = f"""Create a video story plan for:

Story concept: {story_prompt}

Requirements:
- {segment_count} segments of {segment_duration} seconds each
- Total duration: {segment_count * segment_duration} seconds

Generate cinematic prompts with smooth visual transitions between segments.
Each video_prompt should include specific visual details and can include camera commands.
Each narration_text should match the segment duration (~{segment_duration} seconds of speech).
Each end_frame_prompt should describe where the segment visually ends for seamless transition."""

    logger.info(f"Generating video plan: {segment_count} segments of {segment_duration}s each")

    completion = await client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format=VideoStoryPlan,
        temperature=0.7,
    )

    plan = completion.choices[0].message.parsed
    if plan is None:
        raise ValueError("Failed to generate video plan - no response from API")

    logger.info(f"Generated video plan: {plan.title} with {len(plan.segments)} segments")
    return plan
