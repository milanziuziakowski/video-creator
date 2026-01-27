# Video Creator - Complete System Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Component Reference](#component-reference)
4. [AI Prompt Generation](#ai-prompt-generation)
5. [MCP Server Integration](#mcp-server-integration)
6. [Workflow Guide](#workflow-guide)
7. [API Reference](#api-reference)
8. [Development Guide](#development-guide)
9. [Troubleshooting](#troubleshooting)

---

## System Overview

The Video Creator is a Python-based system for generating 1-minute videos using:
- **OpenAI** for AI-powered prompt generation and story planning
- **MiniMax API** for AI-powered image, audio, and video generation
- **FL2V (First-Last Frame Video)** for seamless segment transitions
- **FFmpeg** for deterministic media operations
- **Model Context Protocol (MCP)** for tool integration

### Key Features
- ✅ **AI-powered prompt generation** with OpenAI structured outputs
- ✅ **Automated video planning** with configurable segment durations (6s or 10s)
- ✅ **Voice cloning** from user-provided audio samples
- ✅ **Frame-controlled video generation** ensuring smooth transitions
- ✅ **Human-in-the-loop (HITL)** approval gates for quality control
- ✅ **Deterministic media processing** with FFmpeg
- ✅ **Modular architecture** with MCP server integration
- ✅ **Intelligent continuity** with cinematic visual guidelines

### Constraints
- Maximum video duration: **60 seconds**
- Segment durations: **6 or 10 seconds**
- Per-segment approval required (HITL gate)
- All media operations must be deterministic

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Video Creator Application                  │
│                                                              │
│  ┌──────────────┐      ┌─────────────┐     ┌─────────────┐ │
│  │ Orchestrator │ ───> │ Video Plan  │ ───>│  Segments   │ │
│  └──────────────┘      └─────────────┘     └─────────────┘ │
│         │                                                    │
│         │ Calls MCP Tools                                   │
└─────────┼────────────────────────────────────────────────────┘
          │
          ├──────────────┬──────────────┬─────────────────
          │              │              │
    ┌─────▼─────┐  ┌────▼────┐  ┌─────▼─────┐
    │  MiniMax  │  │  FL2V   │  │ MediaOps  │
    │    MCP    │  │   MCP   │  │    MCP    │
    └───────────┘  └─────────┘  └───────────┘
         │              │              │
    ┌────▼────┐    ┌───▼────┐    ┌───▼────┐
    │ MiniMax │    │MiniMax │    │ FFmpeg │
    │   API   │    │  API   │    │        │
    └─────────┘    └────────┘    └────────┘
```

### Component Layers

1. **Application Layer** (`src/`)
   - Orchestrator: Workflow coordination
   - Models: Data structures (VideoPlan, SegmentStatus)
   - Config: Settings and environment management

2. **Integration Layer** (`mcp_servers/`)
   - MiniMax MCP: AI generation (image, audio, voice cloning)
   - FL2V MCP: Video generation with frame control
   - MediaOps MCP: FFmpeg operations (concat, mux, extract)

3. **External Services**
   - MiniMax API: Cloud AI services
   - FFmpeg: Local media processing
   - Storage: S3/Azure/GCP/Local filesystem

---

## Component Reference

### Orchestrator (`src/core/orchestrator.py`)

Central coordinator for the video creation workflow.

**Key Methods:**
- `create_video_plan()`: Generate segment plan from story prompt
- `clone_voice()`: Clone voice from audio sample
- `process_segment()`: Generate video/audio for single segment
- `finalize_video()`: Concatenate and mux all segments
- `validate_plan()`: Validate plan integrity

**Features:**
- Automatic retry with exponential backoff
- Comprehensive error handling
- Plan persistence (save/load JSON)
- Validation and health checks
- AI-powered prompt generation with fallbacks

### AI Prompt Generator (`src/ai/prompt_generator.py`)

Intelligent prompt generation using OpenAI's structured outputs.

**Key Features:**
- **Structured Outputs**: Uses `beta.chat.completions.parse()` for guaranteed valid Pydantic responses
- **Cinematic Guidelines**: 350+ line system prompt with visual composition, lighting, and continuity rules
- **3-Level Fallback**: Structured outputs → JSON mode → Manual defaults
- **Type Safety**: Pydantic models (`VideoStoryPlan`, `SegmentPrompt`)

**Functions:**
- `generate_story_plan()`: AI-powered prompt generation with structured outputs
- `generate_story_plan_fallback()`: JSON mode fallback for compatibility
- `create_default_prompts()`: Manual fallback with placeholder prompts

**Example:**
```python
from src.ai.prompt_generator import generate_story_plan

plan = await generate_story_plan(
    story_prompt="A peaceful sunrise over mountains",
    segment_count=2,
    segment_duration=6
)
# Returns VideoStoryPlan with intelligent, coherent prompts
```

### Models (`src/models/`)

#### VideoPlan
```python
{
    "project_id": str,
    "target_duration_sec": int,  # ≤ 60
    "segment_len_sec": int,      # 6 or 10
    "segment_count": int,
    "voice_id": Optional[str],
    "segments": List[SegmentStatus],
    "final_video_url": Optional[str]
}
```

#### SegmentStatus
```python
{
    "segment_index": int,
    "prompt": str,
    "narration_text": str,
    "first_frame_image_url": Optional[str],
    "last_frame_image_url": Optional[str],
    "segment_video_url": Optional[str],
    "segment_audio_url": Optional[str],
    "approved": bool,
    "video_duration_sec": Optional[float]
}
```

---

## AI Prompt Generation

### Overview

The system uses OpenAI's structured outputs to generate intelligent, cinematic video prompts with proper visual continuity. This replaces manual prompt writing with AI-powered story planning.

### Architecture

```
Story Prompt → OpenAI (GPT-4o) → Structured Outputs → Pydantic Models → Video Segments
```

**Flow:**
1. User provides high-level story (e.g., "A peaceful sunrise over mountains")
2. System generates comprehensive system prompt with cinematic guidelines
3. OpenAI returns structured JSON validated against Pydantic schema
4. Each segment gets intelligent video prompt + narration text
5. Visual continuity maintained across segments

### Key Features

#### 1. Structured Outputs
Uses OpenAI's `beta.chat.completions.parse()` API for guaranteed valid responses:
```python
completion = await client.beta.chat.completions.parse(
    model="gpt-4o-2024-08-06",
    messages=[{"role": "system", "content": SYSTEM_PROMPT}, ...],
    response_format=VideoStoryPlan  # Pydantic model
)
```

**Benefits:**
- ✅ No JSON parsing errors
- ✅ Schema validation built-in
- ✅ Type-safe responses
- ✅ Automatic retry on validation failure

#### 2. Cinematic System Prompts

**350+ line prompt** covering:
- **Visual Composition**: Rule of thirds, leading lines, depth
- **Camera Movement**: Pans, zooms, tracking shots
- **Lighting**: Golden hour, backlighting, color temperature
- **Continuity**: Last-frame → first-frame transitions
- **Narration**: Voice-over writing principles
- **Technical Constraints**: 6-10 second segments, FL2V requirements

#### 3. Three-Level Fallback Strategy

**Level 1: Structured Outputs (Primary)**
```python
plan = await generate_story_plan(story, segment_count)
# Uses beta.chat.completions.parse() with Pydantic validation
```

**Level 2: JSON Mode Fallback**
```python
plan = await generate_story_plan_fallback(story, segment_count)
# Uses standard completions with JSON mode + manual parsing
```

**Level 3: Manual Defaults**
```python
plan = create_default_prompts(story, segment_count)
# Returns placeholder prompts (always works)
```

### Usage

#### Basic Usage (AI Enabled)

```python
from src.core.orchestrator import VideoOrchestrator
from src.config import Settings

settings = Settings()
orchestrator = VideoOrchestrator(settings)

# AI generates intelligent prompts
plan = await orchestrator.create_video_plan(
    project_id="my_video",
    story_prompt="A journey through an enchanted forest at twilight",
    target_duration_sec=12,
    segment_len_sec=6,
    use_ai=True  # ← Enable AI (default)
)

# Segments now have AI-generated prompts
for segment in plan.segments:
    print(f"Video: {segment.prompt}")
    print(f"Narration: {segment.narration_text}")
```

#### Manual Mode (AI Disabled)

```python
# Fallback to placeholder prompts
plan = await orchestrator.create_video_plan(
    project_id="my_video",
    story_prompt="A journey through an enchanted forest",
    target_duration_sec=12,
    segment_len_sec=6,
    use_ai=False  # ← Disable AI
)
```

### Configuration

**Environment Variables:**
```bash
# Required for AI mode
OPENAI_API_KEY=sk-proj-your-key-here
```

**Settings** (in `src/ai/prompt_generator.py`):
```python
DEFAULT_MODEL = "gpt-4o-2024-08-06"  # Model for structured outputs
MAX_TOKENS = 4000
TEMPERATURE = 0.7
```

### Example Output

**Input Story:**
```
"A peaceful morning as the sun rises over a tranquil ocean"
```

**AI-Generated Segments:**

**Segment 0 (0-6s):**
- **Video Prompt:** Wide establishing shot of a vast, tranquil ocean under a pre-dawn sky. The horizon glows with soft pink and orange hues as the first rays of sunlight begin to appear. Gentle waves lap peacefully against the shore. Camera slowly pans right, capturing the expansive seascape.
- **Narration:** As the first light of dawn breaks across the horizon, the ocean awakens to a new day, its surface shimmering with the promise of morning.

**Segment 1 (6-12s):**
- **Video Prompt:** Continuation from the glowing horizon. Slow zoom into the rising sun as it lifts above the ocean, casting golden reflections across the rippling water. Seabirds silhouette against the brightening sky. Camera maintains smooth zoom motion.
- **Narration:** The sun climbs higher, painting the sky in brilliant gold and amber, as nature orchestrates another perfect sunrise over the peaceful waters.

### Performance

**API Calls:** 1 call per video plan (not per segment)

**Response Time:** ~2-4 seconds for 2-3 segments

**Token Usage:**
- System prompt: ~1,000 tokens
- User message: ~100-200 tokens
- Response: ~200-500 tokens per segment
- **Total: ~1,500-3,000 tokens per plan**

**Cost Estimate** (gpt-4o-2024-08-06, as of Dec 2024):
- Input: $2.50 per 1M tokens
- Output: $10.00 per 1M tokens
- **~$0.01-0.03 per video plan**

### Best Practices

1. **Use AI Mode**: Produces significantly better prompts than manual placeholders
2. **Provide Detailed Stories**: More context = better AI output
3. **Monitor Costs**: Track OpenAI token usage via dashboard
4. **Test Fallbacks**: Ensure manual mode works if API is down
5. **Customize System Prompts**: Edit `SYSTEM_PROMPT` in `prompt_generator.py` for specific styles

### Testing

```bash
# Test AI prompt generation
python test_ai_prompts.py
```

**Expected output:**
- ✅ AI-generated prompts with proper continuity
- ✅ Validation of segment structure
- ✅ Fallback to manual mode if API unavailable

### Troubleshooting

**Issue:** `OPENAI_API_KEY not set`
- **Solution:** Add `OPENAI_API_KEY=sk-proj-...` to `.env` file

**Issue:** API rate limits
- **Solution:** Implement caching or reduce request frequency

**Issue:** Poor quality prompts
- **Solution:** Enhance system prompt or use higher temperature (0.8-0.9)

**Issue:** Inconsistent continuity
- **Solution:** Verify last-frame descriptions are being passed correctly

---

## MCP Server Integration

### MiniMax MCP (`mcp_servers/minimax_mcp/`)

**Tools:**
- `voice_clone(audio_bytes, voice_name)` → voice_id
- `text_to_audio(text, voice_id, language)` → audio_url
- `text_to_image(prompt, width, height)` → image_url
- `query_video_generation(task_id)` → status, video_url

**Environment:**
- `MINIMAX_API_KEY`: Required API key

### FL2V MCP (`mcp_servers/fl2v_mcp/`)

**Tools:**
- `create_fl2v_task(prompt, first_frame, last_frame, duration, model)` → task_id
- `query_task_status(task_id)` → status, video_url

**Features:**
- Base64 or file path support for frames
- Polling with exponential backoff
- Supports 6s and 10s durations
- 512P, 768P, 1080P resolutions

### MediaOps MCP (`mcp_servers/mediaops_mcp/`)

**Tools:**
- `extract_last_frame(video_path, output_path)` → frame_path
- `concat_videos(video_paths[], output_path)` → concatenated_video
- `concat_audios(audio_paths[], output_path)` → concatenated_audio
- `mux_audio_video(video_path, audio_path, output_path)` → final_video
- `normalize_audio(audio_path, output_path, target_db)` → normalized_audio
- `probe_duration(media_path)` → metadata

**Requirements:**
- FFmpeg installed and in PATH
- ffprobe (usually bundled with FFmpeg)

---

## Workflow Guide

### Complete Video Creation Workflow

```
1. INITIALIZATION
   ├─> Load Settings
   ├─> Initialize Orchestrator
   └─> Create project directories

2. PLANNING PHASE
   ├─> Create VideoPlan (story_prompt, duration, segment_len)
   ├─> AI generates segment prompts (OpenAI structured outputs)
   └─> AI generates narration text (OpenAI structured outputs)

3. VOICE CLONING
   ├─> Upload voice sample audio
   ├─> Call voice_clone() → voice_id
   └─> Store voice_id in plan

4. SEGMENT GENERATION (foreach segment)
   ├─> Generate first_frame (segment 0: user-provided, else: last frame of prev)
   ├─> Generate last_frame (text_to_image with end-frame prompt)
   ├─> Create FL2V task (first + last frames)
   ├─> Poll FL2V status until complete → segment_video_url
   ├─> Generate audio (text_to_audio with narration)
   ├─> HITL GATE: User approves/regenerates
   └─> Mark segment as approved

5. FINALIZATION
   ├─> Validate all segments approved
   ├─> Concat all segment videos
   ├─> Concat all segment audios
   ├─> Mux video + audio
   └─> Upload final video to storage

6. DELIVERY
   └─> Return final_video_url
```

### HITL (Human-in-the-Loop) Gate

Each segment requires approval before proceeding:

**Options:**
- ✅ **Approve**: Continue to next segment
- 🔄 **Regenerate**: Retry generation with same prompts
- ✏️ **Edit**: Modify prompts and regenerate

---

## API Reference

### Orchestrator API

#### `create_video_plan()`
```python
await orchestrator.create_video_plan(
    project_id="project_001",
    story_prompt="A journey through nature",
    target_duration_sec=60,
    segment_len_sec=6,
    use_ai=True  # Enable AI prompt generation (default: True)
) → VideoPlan
```

**Parameters:**
- `use_ai` (bool): Use OpenAI for intelligent prompt generation
  - `True`: AI generates cinematic prompts with continuity
  - `False`: Uses placeholder prompts
  - Automatically falls back to placeholders if API unavailable

#### `clone_voice()`
```python
await orchestrator.clone_voice(
    voice_sample_bytes=audio_bytes,
    voice_name="narrator"
) → Optional[str]  # voice_id
```

#### `process_segment()`
```python
await orchestrator.process_segment(
    segment=segment_status,
    voice_id="voice_abc123",
    first_frame_path="/path/to/frame.jpg",
    max_retries=3
) → bool  # success
```

#### `finalize_video()`
```python
await orchestrator.finalize_video(
    video_plan=plan
) → Optional[str]  # final_video_url
```

#### `validate_plan()`
```python
orchestrator.validate_plan(plan) → {
    "valid": bool,
    "issues": List[str],
    "warnings": List[str],
    "segment_count": int,
    "approved_count": int
}
```

---

## Development Guide

### Setup

```bash
# 1. Clone repository
cd video_creator

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -e .

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Verify setup
python -m pytest tests/
```

### Environment Variables

```bash
# Required
MINIMAX_API_KEY=sk-...

# AI Prompt Generation (Optional but Recommended)
OPENAI_API_KEY=sk-proj-...  # For AI-powered prompt generation

# Optional
STORAGE_TYPE=local  # local, s3, azure, gcp
DB_TYPE=postgresql
LOG_LEVEL=INFO
```

### Running MCP Servers

```bash
# MiniMax MCP
python mcp_servers/minimax_mcp/minimax_server.py

# FL2V MCP
python mcp_servers/fl2v_mcp/fl2v_server.py

# MediaOps MCP
python mcp_servers/mediaops_mcp/mediaops_server.py
```

### Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_orchestrator.py

# Run with coverage
pytest --cov=src tests/

# Test workflow end-to-end
python test_video_workflow.py
```

---

## Troubleshooting

### Common Issues

#### 1. MiniMax API Errors
**Symptom:** `MINIMAX_API_KEY not set` or API authentication failures

**Solution:**
```bash
# Verify API key is set
echo $MINIMAX_API_KEY

# Check .env file
cat .env | grep MINIMAX_API_KEY

# Test API connectivity
python -c "import os; print('API Key:', os.getenv('MINIMAX_API_KEY')[:10] + '...')"
```

#### 2. FFmpeg Not Found
**Symptom:** `FFmpegError: ffmpeg command not found`

**Solution:**
```bash
# Install FFmpeg
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
# Windows: Download from ffmpeg.org

# Verify installation
ffmpeg -version
ffprobe -version
```

#### 3. Import Errors with MCP Servers
**Symptom:** `Import "mcp_minimax" could not be resolved`

**Solution:**
- MCP servers are accessed via MCP protocol, not direct Python imports
- Use the MCP tools through the orchestrator or test via MCP client
- For testing, run servers independently and call via MCP

#### 4. Video Generation Timeout
**Symptom:** FL2V tasks stuck in "processing" state

**Solution:**
- Video generation can take 30-60 seconds
- Poll with 10-second intervals
- Check MiniMax API status page
- Verify sufficient API quota

#### 5. Segment Approval Issues
**Symptom:** Cannot finalize video - unapproved segments

**Solution:**
```python
# Check segment status
for seg in plan.segments:
    print(f"Segment {seg.segment_index}: approved={seg.approved}")

# Manually approve segments (development only)
for seg in plan.segments:
    seg.approved = True
```

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or via environment:
```bash
export LOG_LEVEL=DEBUG
```

---

## Performance Tips

1. **Parallel Processing**: Generate multiple segments in parallel (with HITL gates)
2. **Caching**: Store generated frames/audio to avoid regeneration
3. **FFmpeg Optimization**: Use `-c copy` to avoid re-encoding when possible
4. **Storage**: Use cloud storage (S3/Azure) for better scalability
5. **Retry Logic**: Configure appropriate retry attempts and backoff

---

## Roadmap

### Phase 1: Core Functionality (✅ Complete)
- [x] MCP server integration
- [x] Basic orchestrator workflow
- [x] FFmpeg media operations
- [x] Plan persistence

### Phase 2: AI Integration (✅ Complete)
- [x] OpenAI structured outputs for prompt generation
- [x] Intelligent segment planning with continuity
- [x] Cinematic visual guidelines (350+ line prompts)
- [x] 3-level fallback strategy (AI → JSON → Manual)

### Phase 3: UI/UX (Planned)
- [ ] Web UI for HITL approval
- [ ] Real-time preview
- [ ] Drag-and-drop editing

### Phase 4: Advanced Features (Future)
- [ ] Multi-voice support
- [ ] Background music integration
- [ ] Automatic subtitle generation
- [ ] Template library

---

## License

Copyright © 2026. All rights reserved.

---

## Support

For issues and questions:
- Check [Troubleshooting](#troubleshooting) section
- Review MCP server logs
- Consult [ARCHITECTURE.md](ARCHITECTURE.md) for design details
