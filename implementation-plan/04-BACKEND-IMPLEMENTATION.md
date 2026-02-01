# Backend Implementation Guide

**Phase:** 4  
**Technology:** Python 3.11+, FastAPI, OpenAI Agents SDK, MiniMax API

---

## 1. Project Setup

### 1.1 Manual Steps (wymagane przed rozpoczęciem)

```bash
# 1. Create new project directory
mkdir ai-video-creator-backend
cd ai-video-creator-backend

# 2. Initialize Python project with uv (recommended) or venv
uv init
uv venv
.venv\Scripts\activate  # Windows

# 3. Install core dependencies
uv add fastapi uvicorn python-dotenv pydantic pydantic-settings
uv add sqlalchemy alembic asyncpg  # Database
uv add httpx aiofiles              # HTTP client & file handling
uv add openai-agents               # OpenAI Agents SDK
uv add python-multipart            # File uploads
uv add python-jose[cryptography]   # JWT handling

# 4. Install dev dependencies
uv add --dev pytest pytest-asyncio pytest-cov httpx

# 5. Create .env file
cp .env.example .env
# Fill in your API keys

# 6. Initialize database
alembic init migrations
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### 1.2 Environment Variables (.env.example)

```bash
# ============================================================================
# Application
# ============================================================================
APP_NAME=AI-Video-Creator
APP_ENV=development
DEBUG=true

# ============================================================================
# API Keys
# ============================================================================
# Get your API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-your-openai-api-key

# Get your API key from: https://platform.minimaxi.com/
MINIMAX_API_KEY=sk-api-your-minimax-api-key

# ============================================================================
# Azure Entra ID (for token validation)
# ============================================================================
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id

# ============================================================================
# Database Configuration
# ============================================================================
# Production: postgresql+asyncpg://user:password@localhost:5432/video_creator
# Development: sqlite+aiosqlite:///./video_creator.db
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/video_creator

# ============================================================================
# Storage Configuration
# ============================================================================
STORAGE_PATH=./storage
UPLOAD_MAX_SIZE_MB=20

# ============================================================================
# CORS Configuration
# ============================================================================
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# ============================================================================
# MCP Server Settings (for MCP tools)
# ============================================================================
MCP_TRANSPORT=stdio
MCP_LOG_LEVEL=DEBUG
LOG_LEVEL=INFO

# ============================================================================
# FFmpeg Configuration (for mediaops_mcp)
# ============================================================================
# FFmpeg binary path (leave empty to use system PATH)
FFMPEG_PATH=
FFPROBE_PATH=
```

---

## 2. Core Application Structure

### 2.1 Main Application (app/main.py)

```python
"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1.router import api_router
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description="AI Video Creator - 1-Minute Video Studio",
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API router
    app.include_router(api_router, prefix="/api/v1")
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

### 2.2 Configuration (app/config.py)

```python
"""Application configuration using pydantic-settings."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    APP_NAME: str = "AI Video Creator"
    APP_ENV: str = "development"
    DEBUG: bool = False
    
    # API Keys
    OPENAI_API_KEY: str = ""
    MINIMAX_API_KEY: str = ""
    
    # Azure Entra ID
    AZURE_TENANT_ID: str = ""
    AZURE_CLIENT_ID: str = ""
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./video_creator.db"
    
    # Storage
    STORAGE_PATH: Path = Path("./storage")
    UPLOAD_MAX_SIZE_MB: int = 20
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"
    
    @property
    def storage_uploads(self) -> Path:
        path = self.STORAGE_PATH / "uploads"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def storage_temp(self) -> Path:
        path = self.STORAGE_PATH / "temp"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def storage_output(self) -> Path:
        path = self.STORAGE_PATH / "output"
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
```

---

## 3. Database Models

### 3.1 SQLAlchemy Base (app/db/base.py)

```python
"""SQLAlchemy base configuration."""

from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 3.2 Project Model (app/db/models/project.py)

```python
"""Project database model."""

from enum import Enum
from sqlalchemy import Column, String, Integer, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class ProjectStatus(str, Enum):
    CREATED = "created"
    MEDIA_UPLOADED = "media_uploaded"
    VOICE_CLONING = "voice_cloning"
    PLAN_GENERATING = "plan_generating"
    PLAN_READY = "plan_ready"
    GENERATING = "generating"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"


class Project(Base, TimestampMixin):
    """Project database model."""
    
    __tablename__ = "projects"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    story_prompt = Column(Text)
    
    target_duration_sec = Column(Integer, default=60)
    segment_len_sec = Column(Integer, default=6)
    segment_count = Column(Integer, default=0)
    
    voice_id = Column(String(255))
    first_frame_url = Column(String(1024))
    audio_sample_url = Column(String(1024))
    final_video_url = Column(String(1024))
    
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.CREATED)
    
    # Relationships
    user = relationship("User", back_populates="projects")
    segments = relationship("Segment", back_populates="project", cascade="all, delete-orphan")
```

### 3.3 Segment Model (app/db/models/segment.py)

```python
"""Segment database model."""

from enum import Enum
from sqlalchemy import Column, String, Integer, Boolean, Enum as SQLEnum, ForeignKey, Text, Float
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class SegmentStatus(str, Enum):
    PENDING = "pending"
    PROMPT_READY = "prompt_ready"
    APPROVED = "approved"
    GENERATING = "generating"
    GENERATED = "generated"
    SEGMENT_APPROVED = "segment_approved"
    FAILED = "failed"


class Segment(Base, TimestampMixin):
    """Segment database model."""
    
    __tablename__ = "segments"
    
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    
    index = Column(Integer, nullable=False)
    video_prompt = Column(Text)
    narration_text = Column(Text)
    end_frame_prompt = Column(Text)
    
    first_frame_url = Column(String(1024))
    last_frame_url = Column(String(1024))
    video_url = Column(String(1024))
    audio_url = Column(String(1024))
    
    video_duration_sec = Column(Float)
    
    status = Column(SQLEnum(SegmentStatus), default=SegmentStatus.PENDING)
    approved = Column(Boolean, default=False)
    
    # Relationships
    project = relationship("Project", back_populates="segments")
```

---

## 4. Pydantic Models (API Schemas)

### 4.1 Project Schemas (app/models/project.py)

```python
"""Project Pydantic models for API."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.db.models.project import ProjectStatus


class ProjectBase(BaseModel):
    """Base project schema."""
    
    name: str = Field(..., min_length=1, max_length=255)
    story_prompt: Optional[str] = None
    target_duration_sec: int = Field(60, ge=6, le=60)
    segment_len_sec: int = Field(6, ge=6, le=10)


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""
    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    story_prompt: Optional[str] = None


class SegmentSummary(BaseModel):
    """Brief segment info for project listing."""
    
    id: str
    index: int
    status: str
    approved: bool
    
    class Config:
        from_attributes = True


class ProjectResponse(ProjectBase):
    """Schema for project response."""
    
    id: str
    user_id: str
    segment_count: int
    voice_id: Optional[str]
    first_frame_url: Optional[str]
    audio_sample_url: Optional[str]
    final_video_url: Optional[str]
    status: ProjectStatus
    segments: List[SegmentSummary] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Schema for project list response."""
    
    projects: List[ProjectResponse]
    total: int
```

### 4.2 Generation Schemas (app/models/generation.py)

```python
"""Generation-related Pydantic models."""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class GenerationStatus(str, Enum):
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    SUCCESS = "Success"
    FAIL = "Fail"


class VideoPlanSegment(BaseModel):
    """Single segment in a video plan."""
    
    segment_index: int
    video_prompt: str
    narration_text: str
    end_frame_prompt: str


class VideoPlanResponse(BaseModel):
    """Response from AI video plan generation."""
    
    title: str
    segments: List[VideoPlanSegment]
    continuity_notes: str


class GeneratePlanRequest(BaseModel):
    """Request to generate AI video plan."""
    
    project_id: str
    story_prompt: str


class GenerateSegmentRequest(BaseModel):
    """Request to generate a single segment."""
    
    segment_id: str


class GenerationStatusResponse(BaseModel):
    """Response for generation status polling."""
    
    task_id: str
    status: GenerationStatus
    file_id: Optional[str] = None
    download_url: Optional[str] = None
    error: Optional[str] = None
    progress: Optional[int] = None  # 0-100


class FL2VResolution(str, Enum):
    """Supported resolutions for First & Last Frame video generation."""
    RES_768P = "768P"
    RES_1080P = "1080P"
    # Note: 512P is NOT supported for FL2V


class CameraCommand(str, Enum):
    """Camera movement commands for MiniMax video generation prompts."""
    TRUCK_LEFT = "[Truck left]"
    TRUCK_RIGHT = "[Truck right]"
    PAN_LEFT = "[Pan left]"
    PAN_RIGHT = "[Pan right]"
    PUSH_IN = "[Push in]"
    PULL_OUT = "[Pull out]"
    PEDESTAL_UP = "[Pedestal up]"
    PEDESTAL_DOWN = "[Pedestal down]"
    TILT_UP = "[Tilt up]"
    TILT_DOWN = "[Tilt down]"
    ZOOM_IN = "[Zoom in]"
    ZOOM_OUT = "[Zoom out]"
    SHAKE = "[Shake]"
    TRACKING_SHOT = "[Tracking shot]"
    STATIC_SHOT = "[Static shot]"


class FL2VGenerateRequest(BaseModel):
    """Request to generate First & Last Frame video (FL2V).
    
    Uses MiniMax Hailuo API endpoint: POST /v1/video_generation
    
    Image Requirements:
        - Formats: JPG, JPEG, PNG, WebP
        - Size: < 20MB each
        - Dimensions: Short side > 300px, Aspect ratio 2:5 to 5:2
    """
    
    segment_id: str
    prompt: str = Field(
        default="",
        max_length=2000,
        description="Video description. Can include camera commands like [Zoom in], [Pan left]"
    )
    first_frame_image: Optional[str] = Field(
        default=None,
        description="URL or base64 data URL (data:image/jpeg;base64,...) of first frame"
    )
    last_frame_image: str = Field(
        ...,
        description="Required. URL or base64 data URL of last frame"
    )
    duration: int = Field(
        default=6,
        ge=6,
        le=10,
        description="Video duration in seconds (6 or 10)"
    )
    resolution: FL2VResolution = Field(
        default=FL2VResolution.RES_768P,
        description="Video resolution (768P or 1080P - 512P not supported for FL2V)"
    )
    prompt_optimizer: bool = Field(
        default=True,
        description="Auto-optimize prompt. Set False for precise control"
    )
    camera_commands: Optional[List[CameraCommand]] = Field(
        default=None,
        max_length=3,
        description="Camera commands to append to prompt (max 3 simultaneous)"
    )
    
    def get_prompt_with_commands(self) -> str:
        """Get prompt with camera commands appended."""
        if not self.camera_commands:
            return self.prompt
        commands = ",".join([cmd.value.strip("[]") for cmd in self.camera_commands])
        return f"{self.prompt} [{commands}]"


class FL2VGenerateResponse(BaseModel):
    """Response from FL2V video generation task creation."""
    
    task_id: str
    segment_id: str
    status: str = "submitted"
    model: str = "MiniMax-Hailuo-02"
```

---

## 5. OpenAI Agents Integration

### 5.1 Supervisor Agent (app/agents/supervisor_agent.py)

```python
"""Supervisor Agent for video planning using OpenAI Agents SDK."""

from typing import List
from pydantic import BaseModel, Field
from agents import Agent, function_tool, Runner

from app.config import settings


class SegmentPrompt(BaseModel):
    """Schema for a single segment prompt."""
    
    segment_index: int = Field(..., description="0-indexed segment number")
    video_prompt: str = Field(..., description="Detailed visual description for video generation")
    narration_text: str = Field(..., description="Voice-over narration text")
    end_frame_prompt: str = Field(..., description="Description of the final frame")


class VideoStoryPlan(BaseModel):
    """Complete video story plan."""
    
    title: str = Field(..., description="Video title")
    segments: List[SegmentPrompt] = Field(..., description="List of segment prompts")
    continuity_notes: str = Field(..., description="Notes about visual continuity")


# Define tools for the agent
@function_tool
def create_video_plan(
    story_concept: str,
    segment_count: int,
    segment_duration: int,
) -> VideoStoryPlan:
    """Create a complete video story plan with prompts for each segment.
    
    Args:
        story_concept: The user's story idea or concept
        segment_count: Number of segments to create
        segment_duration: Duration of each segment in seconds (6 or 10)
        
    Returns:
        VideoStoryPlan with all segments
    """
    # This will be filled by the agent's response
    pass


# Create the Supervisor Agent
supervisor_agent = Agent(
    name="Video Story Supervisor",
    instructions="""You are an expert video story planner specializing in creating cohesive, 
visually compelling narratives for short-form video content.

IMPORTANT: Generate all output in POLISH language.

Your responsibilities:
1. Break down story concepts into cinematic segments
2. Write detailed video prompts suitable for AI video generation
3. Ensure visual continuity between segments (end frame → next start frame)
4. Write compelling voice-over narration that matches the visuals
5. Maintain consistent tone and style throughout

Guidelines for video prompts:
- Be specific about scene composition, lighting, colors, and camera movement
- Include emotional tone and atmosphere
- Describe actions and movements clearly
- Each prompt should naturally flow from the previous segment's end frame

Guidelines for narration:
- Keep it natural and conversational
- Match pacing to the segment duration
- Complement visuals without redundancy
- Ensure narrative arc across all segments

Total video duration constraint: segment_count × segment_duration seconds

All text must be in Polish language (video prompts, narration, and end-frame descriptions).""",
    tools=[create_video_plan],
    model="gpt-4o",  # Best for structured outputs
)


async def generate_video_plan(
    story_prompt: str,
    segment_count: int,
    segment_duration: int,
) -> VideoStoryPlan:
    """Generate a complete video plan using the Supervisor Agent.
    
    Args:
        story_prompt: User's story concept
        segment_count: Number of segments
        segment_duration: Duration per segment
        
    Returns:
        VideoStoryPlan with all segment prompts
    """
    user_message = f"""Create a video story plan for the following concept:

Story: {story_prompt}

Requirements:
- Number of segments: {segment_count}
- Each segment duration: {segment_duration} seconds
- Total video duration: {segment_count * segment_duration} seconds

Please generate detailed video prompts, narration text, and end-frame descriptions 
for each segment, ensuring smooth visual transitions between segments."""

    result = await Runner.run(
        supervisor_agent,
        user_message,
    )
    
    # Parse the result into VideoStoryPlan
    # The agent should return a structured response matching our schema
    return result.final_output_as(VideoStoryPlan)
```

### 5.2 Alternative: Using Structured Outputs (app/agents/plan_generator.py)

```python
"""Video plan generator using OpenAI Structured Outputs (simpler approach)."""

from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from typing import List

from app.config import settings


class SegmentPrompt(BaseModel):
    """Single segment prompt schema."""
    
    segment_index: int
    video_prompt: str
    narration_text: str
    end_frame_prompt: str


class VideoStoryPlan(BaseModel):
    """Complete video plan schema."""
    
    title: str
    segments: List[SegmentPrompt]
    continuity_notes: str


SYSTEM_PROMPT = """You are an expert video story planner specializing in creating cohesive, 
visually compelling narratives for short-form video content.

IMPORTANT: Generate all output in POLISH language.

Your task is to break down a user's story concept into video segments with:
1. Detailed video prompts (scene composition, lighting, camera movement, atmosphere)
2. Voice-over narration text
3. End-frame descriptions for seamless transitions

Guidelines:
- Each video prompt should be 2-3 sentences with specific visual details
- Narration should be natural and match the segment duration
- End-frame prompts describe the last frame to ensure smooth transition to the next segment
- Maintain consistent visual style and narrative arc throughout

All text must be in Polish language (video prompts, narration, and end-frame descriptions)."""


async def generate_video_plan(
    story_prompt: str,
    segment_count: int,
    segment_duration: int,
) -> VideoStoryPlan:
    """Generate video plan using OpenAI structured outputs.
    
    This is a simpler alternative to using the full Agents SDK
    when you don't need agent loops or handoffs.
    """
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    user_message = f"""Create a video story plan for:

Story concept: {story_prompt}

Requirements:
- {segment_count} segments of {segment_duration} seconds each
- Total duration: {segment_count * segment_duration} seconds

Generate cinematic prompts with smooth visual transitions."""

    completion = await client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        response_format=VideoStoryPlan,
        temperature=0.7,
    )
    
    return completion.choices[0].message.parsed
```

---

## 6. MiniMax API Client

### 6.1 MiniMax Client (app/integrations/minimax_client.py)

```python
"""MiniMax API client for video and audio generation."""

import asyncio
import base64
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

MINIMAX_API_BASE = "https://api.minimax.io/v1"
TIMEOUT = httpx.Timeout(120.0, connect=30.0)


class MinimaxClient:
    """Client for MiniMax API operations."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.MINIMAX_API_KEY
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request to MiniMax API."""
        url = f"{MINIMAX_API_BASE}{endpoint}"
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.request(
                method,
                url,
                headers=self._headers,
                **kwargs
            )
            
            if response.status_code != 200:
                logger.error(f"MiniMax API error: {response.status_code} - {response.text}")
                raise Exception(f"MiniMax API error: {response.text}")
            
            data = response.json()
            
            # Check for API-level errors
            if data.get("base_resp", {}).get("status_code") != 0:
                error_msg = data.get("base_resp", {}).get("status_msg", "Unknown error")
                raise Exception(f"MiniMax API error: {error_msg}")
            
            return data
    
    # -------------------------------------------------------------------------
    # File Operations
    # -------------------------------------------------------------------------
    
    async def upload_file(
        self,
        file_bytes: bytes,
        filename: str,
        purpose: str = "voice_clone"
    ) -> str:
        """Upload file to MiniMax and return file_id.
        
        Args:
            file_bytes: File content as bytes
            filename: Original filename
            purpose: Purpose of upload (voice_clone, prompt_audio)
            
        Returns:
            file_id string
        """
        url = f"{MINIMAX_API_BASE}/files/upload"
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                files={"file": (filename, file_bytes)},
                data={"purpose": purpose}
            )
            
            data = response.json()
            
            if data.get("base_resp", {}).get("status_code") != 0:
                raise Exception(f"Upload failed: {data}")
            
            return data["file"]["file_id"]
    
    async def retrieve_file(self, file_id: str) -> str:
        """Get download URL for a file.
        
        Args:
            file_id: MiniMax file ID
            
        Returns:
            Download URL
        """
        data = await self._request(
            "GET",
            "/files/retrieve",
            params={"file_id": file_id}
        )
        return data["file"]["download_url"]
    
    # -------------------------------------------------------------------------
    # Voice Operations
    # -------------------------------------------------------------------------
    
    async def voice_clone(
        self,
        file_id: str,
        voice_id: str,
        noise_reduction: bool = True,
        volume_normalization: bool = True,
    ) -> str:
        """Clone voice from uploaded audio file.
        
        Args:
            file_id: ID of uploaded audio file
            voice_id: Desired voice ID (alphanumeric)
            noise_reduction: Apply noise reduction
            volume_normalization: Apply volume normalization
            
        Returns:
            voice_id string (same as input if successful)
        """
        data = await self._request(
            "POST",
            "/voice_clone",
            json={
                "file_id": file_id,
                "voice_id": voice_id,
                "need_noise_reduction": noise_reduction,
                "need_volume_normalization": volume_normalization,
            }
        )
        return voice_id
    
    async def text_to_audio(
        self,
        text: str,
        voice_id: str,
        model: str = "speech-02-hd",
        speed: float = 1.0,
        output_format: str = "mp3",
    ) -> bytes:
        """Generate audio from text using cloned voice.
        
        Args:
            text: Text to convert to speech
            voice_id: Cloned voice ID
            model: TTS model to use
            speed: Speech speed (0.5-2.0)
            output_format: Output format (mp3, wav, etc.)
            
        Returns:
            Audio bytes
        """
        url = f"{MINIMAX_API_BASE}/t2a_v2"
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                url,
                headers=self._headers,
                json={
                    "model": model,
                    "text": text,
                    "voice_setting": {
                        "voice_id": voice_id,
                        "speed": speed,
                    },
                    "audio_setting": {
                        "format": output_format,
                    }
                }
            )
            
            # For streaming audio, MiniMax returns binary directly
            # or JSON with base64 encoded audio
            content_type = response.headers.get("content-type", "")
            
            if "audio" in content_type:
                return response.content
            else:
                data = response.json()
                if "data" in data and "audio" in data["data"]:
                    return base64.b64decode(data["data"]["audio"])
                raise Exception(f"Unexpected TTS response: {data}")
    
    # -------------------------------------------------------------------------
    # Video Operations - First & Last Frame Video Generation (FL2V)
    # -------------------------------------------------------------------------
    
    async def generate_video_fl2v(
        self,
        prompt: str,
        last_frame_image: str,
        first_frame_image: Optional[str] = None,
        model: str = "MiniMax-Hailuo-02",
        duration: int = 6,
        resolution: str = "768P",
        prompt_optimizer: bool = True,
        callback_url: Optional[str] = None,
    ) -> str:
        """Start First & Last Frame video generation task (FL2V).
        
        Args:
            prompt: Video generation prompt (max 2000 chars). 
                   Can include camera commands like [Zoom in], [Pan left], etc.
            last_frame_image: Required. URL or base64 data URL of last frame
                             Format: URL or "data:image/jpeg;base64,..."
            first_frame_image: Optional. URL or base64 data URL of first frame
            model: Video model - must be "MiniMax-Hailuo-02" for FL2V
            duration: Video duration in seconds (6 or 10 for FL2V)
            resolution: Video resolution (768P or 1080P - 512P NOT supported for FL2V)
            prompt_optimizer: Auto-optimize prompt (default True, set False for precise control)
            callback_url: Optional webhook URL for async status updates
            
        Returns:
            task_id for polling
            
        Image Requirements:
            - Formats: JPG, JPEG, PNG, WebP
            - Size: < 20MB
            - Dimensions: Short side > 300px, Aspect ratio 2:5 to 5:2
            - Note: Video resolution follows first_frame_image
            - Note: last_frame_image will be cropped to match first_frame dimensions
            
        Camera Commands (embed in prompt with [command] syntax):
            - Truck: [Truck left], [Truck right]
            - Pan: [Pan left], [Pan right]  
            - Push: [Push in], [Pull out]
            - Pedestal: [Pedestal up], [Pedestal down]
            - Tilt: [Tilt up], [Tilt down]
            - Zoom: [Zoom in], [Zoom out]
            - Shake: [Shake]
            - Follow: [Tracking shot]
            - Static: [Static shot]
            
            Combine up to 3: [Pan left,Pedestal up]
            Sequential: "...[Push in], then...[Pull out]"
        """
        payload = {
            "model": model,
            "last_frame_image": last_frame_image,  # Required for FL2V
            "duration": duration,
            "resolution": resolution,
            "prompt_optimizer": prompt_optimizer,
        }
        
        if prompt:
            payload["prompt"] = prompt[:2000]  # Max 2000 characters
        
        if first_frame_image:
            payload["first_frame_image"] = first_frame_image
        
        if callback_url:
            payload["callback_url"] = callback_url
        
        data = await self._request("POST", "/video_generation", json=payload)
        return data["task_id"]
    
    async def generate_video(
        self,
        prompt: str,
        first_frame_image: str,
        last_frame_image: Optional[str] = None,
        model: str = "MiniMax-Hailuo-02",
        duration: int = 6,
        resolution: str = "720P",
    ) -> str:
        """Start video generation task.
        
        Args:
            prompt: Video generation prompt
            first_frame_image: URL or base64 of first frame
            last_frame_image: URL or base64 of last frame (optional)
            model: Video model to use
            duration: Video duration in seconds (6 or 10)
            resolution: Video resolution
            
        Returns:
            task_id for polling
        """
        payload = {
            "prompt": prompt,
            "first_frame_image": first_frame_image,
            "model": model,
            "duration": duration,
            "resolution": resolution,
        }
        
        if last_frame_image:
            payload["last_frame_image"] = last_frame_image
        
        data = await self._request("POST", "/video_generation", json=payload)
        return data["task_id"]
    
    async def query_video_status(self, task_id: str) -> Dict[str, Any]:
        """Query video generation status.
        
        Args:
            task_id: Task ID from generate_video
            
        Returns:
            Dict with status, file_id (if complete), error (if failed)
        """
        data = await self._request(
            "GET",
            "/query/video_generation",
            params={"task_id": task_id}
        )
        
        return {
            "task_id": task_id,
            "status": data.get("status", "unknown"),
            "file_id": data.get("file_id"),
        }
    
    async def poll_video_until_complete(
        self,
        task_id: str,
        interval: float = 10.0,
        max_attempts: int = 60,
    ) -> Dict[str, Any]:
        """Poll video generation until complete or failed.
        
        Args:
            task_id: Task ID to poll
            interval: Seconds between polls (recommended: 10)
            max_attempts: Maximum polling attempts
            
        Returns:
            Final status with file_id or error
        """
        for attempt in range(max_attempts):
            status = await self.query_video_status(task_id)
            
            if status["status"] == "Success":
                # Get download URL
                download_url = await self.retrieve_file(status["file_id"])
                status["download_url"] = download_url
                return status
            
            elif status["status"] == "Fail":
                raise Exception(f"Video generation failed: {status}")
            
            # Still processing
            logger.info(f"Video generation in progress... attempt {attempt + 1}")
            await asyncio.sleep(interval)
        
        raise Exception(f"Video generation timed out after {max_attempts} attempts")


# Global client instance
minimax_client = MinimaxClient()
```

---

## 7. API Endpoints

### 7.1 Projects Router (app/api/v1/projects.py)

```python
"""Projects API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse
)
from app.services.project_service import ProjectService
from app.db.models.user import User

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all projects for the current user."""
    service = ProjectService(db)
    projects, total = await service.list_projects(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    return ProjectListResponse(projects=projects, total=total)


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new project."""
    service = ProjectService(db)
    project = await service.create_project(
        user_id=current_user.id,
        data=project_data,
    )
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get project by ID."""
    service = ProjectService(db)
    project = await service.get_project(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update project."""
    service = ProjectService(db)
    project = await service.update_project(project_id, current_user.id, project_data)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete project and all associated data."""
    service = ProjectService(db)
    success = await service.delete_project(project_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")


@router.post("/{project_id}/finalize", response_model=ProjectResponse)
async def finalize_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Finalize project - concatenate and mux all segments."""
    service = ProjectService(db)
    project = await service.finalize_project(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
```

### 7.2 Generation Router (app/api/v1/generation.py)

```python
"""Generation API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.generation import (
    GeneratePlanRequest, VideoPlanResponse,
    GenerateSegmentRequest, GenerationStatusResponse,
)
from app.services.orchestrator_service import OrchestratorService
from app.db.models.user import User

router = APIRouter(prefix="/generation", tags=["generation"])


@router.post("/plan", response_model=VideoPlanResponse)
async def generate_video_plan(
    request: GeneratePlanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate AI video plan for a project."""
    service = OrchestratorService(db)
    
    try:
        plan = await service.generate_video_plan(
            project_id=request.project_id,
            user_id=current_user.id,
            story_prompt=request.story_prompt,
        )
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice-clone")
async def clone_voice(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Clone voice from project's audio sample."""
    service = OrchestratorService(db)
    
    try:
        voice_id = await service.clone_voice(project_id, current_user.id)
        return {"voice_id": voice_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/segment/{segment_id}")
async def generate_segment(
    segment_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start segment generation (video + audio)."""
    service = OrchestratorService(db)
    
    try:
        task_id = await service.start_segment_generation(
            segment_id=segment_id,
            user_id=current_user.id,
        )
        return {"task_id": task_id, "status": "submitted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}", response_model=GenerationStatusResponse)
async def get_generation_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    """Poll generation task status."""
    service = OrchestratorService(None)  # Stateless for polling
    
    try:
        status = await service.get_generation_status(task_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 8. Testing

### 8.1 Test Configuration (tests/conftest.py)

```python
"""Pytest configuration and fixtures."""

import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.config import settings
from app.db.base import Base
from app.api.deps import get_db, get_current_user


# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(engine):
    """Create test database session."""
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def mock_user():
    """Create mock authenticated user."""
    from app.db.models.user import User
    return User(
        id="test-user-id",
        entra_id="test-entra-id",
        email="test@example.com",
        name="Test User",
    )


@pytest.fixture
async def client(db_session, mock_user):
    """Create test client with mocked dependencies."""
    
    async def override_get_db():
        yield db_session
    
    async def override_get_current_user():
        return mock_user
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()
```

### 8.2 E2E Test Example (tests/e2e/test_workflow.py)

```python
"""End-to-end workflow tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_complete_workflow(client: AsyncClient):
    """Test complete video creation workflow."""
    
    # 1. Create project
    response = await client.post("/api/v1/projects/", json={
        "name": "Test Video Project",
        "story_prompt": "A beautiful sunset over the ocean",
        "target_duration_sec": 12,
        "segment_len_sec": 6,
    })
    assert response.status_code == 201
    project = response.json()
    project_id = project["id"]
    
    # 2. Upload first frame (mock)
    # ... upload logic ...
    
    # 3. Generate AI plan
    response = await client.post("/api/v1/generation/plan", json={
        "project_id": project_id,
        "story_prompt": "A beautiful sunset over the ocean",
    })
    assert response.status_code == 200
    plan = response.json()
    assert len(plan["segments"]) == 2
    
    # 4. Approve first segment
    segment_id = project["segments"][0]["id"]
    response = await client.post(f"/api/v1/segments/{segment_id}/approve")
    assert response.status_code == 200
    
    # 5. Generate segment
    response = await client.post(f"/api/v1/generation/segment/{segment_id}")
    assert response.status_code == 200
    task_id = response.json()["task_id"]
    
    # 6. Poll status (mock)
    response = await client.get(f"/api/v1/generation/status/{task_id}")
    assert response.status_code == 200
    
    # ... continue workflow ...
    
    # 7. Finalize project
    response = await client.post(f"/api/v1/projects/{project_id}/finalize")
    assert response.status_code == 200
    assert response.json()["final_video_url"] is not None
```

---

## 9. Next Steps

After implementing the backend:

1. **Run locally:**
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Run tests:**
   ```bash
   pytest tests/ -v
   ```

3. **API documentation:**
   - OpenAPI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

4. **Proceed to Frontend Implementation:**
   - See [05-FRONTEND-IMPLEMENTATION.md](./05-FRONTEND-IMPLEMENTATION.md)
