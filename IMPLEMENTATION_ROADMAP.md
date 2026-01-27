# Implementation Roadmap

## Phase 1: MCP Server Basics ✅ DONE

### Deliverables Completed
- [x] FastMCP server skeletons (minimax, mediaops, fl2v)
- [x] Type-hinted async tool definitions
- [x] Logging configuration (stderr only)
- [x] Project structure with proper organization
- [x] Dependencies in pyproject.toml
- [x] Documentation (architecture, setup, roadmap)

### Files Created
```
src/main.py                           # Entry point
src/config.py                         # Configuration
src/models/segment.py                 # Segment schema
src/models/video_plan.py              # VideoPlan schema
src/core/orchestrator.py              # Orchestrator skeleton
mcp_servers/minimax_mcp/minimax_server.py
mcp_servers/mediaops_mcp/mediaops_server.py
mcp_servers/fl2v_mcp/fl2v_server.py
docs/MCP_SETUP.md                     # MCP detailed guide
docs/PROJECT_SETUP_COMPLETE.md        # Setup summary
README.md                             # Root level README
src/README.md                         # Dev guide
```

---

## Phase 2: MediaOps MCP Implementation

### Objective
Implement FFmpeg wrapper for deterministic media operations.

**Why start here?**
- No external API keys required
- Can test with sample videos
- Enables testing of orchestrator integration

### Tools to Implement

```python
# mcp_servers/mediaops_mcp/mediaops_server.py

@mcp.tool()
async def extract_last_frame(video_path: str, output_path: str) -> dict
    """Extract last frame from video using FFmpeg"""
    # ffmpeg -sseof -5 -i {video_path} -update 1 -q:v 1 {output_path}

@mcp.tool()
async def concat_videos(video_paths: list[str], output_path: str) -> dict
    """Concatenate videos using FFmpeg concat demuxer"""
    # 1. Create concat file list: "file 'path1.mp4'\nfile 'path2.mp4'"
    # 2. ffmpeg -f concat -safe 0 -i list.txt -c copy {output_path}

@mcp.tool()
async def concat_audios(audio_paths: list[str], output_path: str) -> dict
    """Concatenate audio files"""
    # Similar to concat_videos

@mcp.tool()
async def mux_audio_video(video_path: str, audio_path: str, output_path: str) -> dict
    """Mux audio and video into final file"""
    # ffmpeg -i {video_path} -i {audio_path} -c:v copy -c:a copy {output_path}

@mcp.tool()
async def normalize_audio(audio_path: str, output_path: str, target_loudness_db: float) -> dict
    """Normalize audio using loudnorm filter"""
    # ffmpeg -i {audio_path} -af loudnorm=I={target_loudness_db} {output_path}

@mcp.tool()
async def probe_duration(media_path: str) -> dict
    """Get duration and metadata using ffprobe"""
    # ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1
```

### Implementation Pattern

```python
# mcp_servers/mediaops_mcp/ffmpeg_wrapper.py
import subprocess
import json
import logging

logger = logging.getLogger(__name__)

async def run_ffmpeg_command(args: list[str]) -> dict:
    """Execute FFmpeg command and return result"""
    try:
        result = subprocess.run(
            ["ffmpeg"] + args,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes max
        )
        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")
        return {"success": True, "output": result.stdout}
    except Exception as e:
        logger.error(f"FFmpeg command failed: {e}")
        raise

async def extract_last_frame_impl(video_path: str, output_path: str) -> str:
    """Actual implementation"""
    # Validate input file exists
    # Run: ffmpeg -sseof -5 -i {video_path} -update 1 -q:v 1 {output_path}
    # Validate output file created
    # Return output_path
    pass

async def probe_duration_impl(media_path: str) -> float:
    """Actual implementation"""
    # Run ffprobe
    # Parse JSON output
    # Extract duration field
    # Return float
    pass
```

### Deliverables
- [ ] `mcp_servers/mediaops_mcp/ffmpeg_wrapper.py` — FFmpeg command execution
- [ ] `mcp_servers/mediaops_mcp/validators.py` — Input/output validation
- [ ] All 6 tools implemented and tested
- [ ] Unit tests with sample videos
- [ ] Can run: `uv run mediaops_server.py` successfully

### Estimated Effort: 2-3 hours

### Testing
```bash
cd mcp_servers/mediaops_mcp
uv run mediaops_server.py  # Should listen on stdio

# In another terminal, send JSON-RPC requests:
# {"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "probe_duration", "arguments": {"media_path": "test.mp4"}}, "id": 1}
```

---

## Phase 3: Orchestrator Integration

### Objective
Wire up orchestrator to communicate with MCP servers.

### Key Components

```python
# src/core/orchestrator.py

class VideoOrchestrator:
    
    async def create_video_plan(...) -> VideoPlan:
        """Delegate to Supervisor Agent (placeholder for now)"""
        # Create VideoPlan with N segments
        # Store in database
        pass
    
    async def clone_voice(voice_sample_url: str) -> str:
        """Call MiniMax MCP voice_clone tool (placeholder)"""
        # Will be implemented in Phase 4
        pass
    
    async def process_segment(segment: SegmentStatus) -> bool:
        """Full segment workflow"""
        # 1. Generate end_frame_image (Frame Designer Agent)
        # 2. Call FL2V MCP: create_fl2v_task()
        # 3. Call MiniMax MCP: text_to_audio()
        # 4. Present to HITL gate
        # 5. Loop if regenerate
        pass
    
    async def finalize_video(video_plan: VideoPlan) -> str:
        """Concat and mux"""
        # 1. Get all segment video paths
        # 2. Call MediaOps MCP: concat_videos()
        # 3. Get all segment audio paths
        # 4. Call MediaOps MCP: concat_audios()
        # 5. Call MediaOps MCP: mux_audio_video()
        # 6. Upload final video
        # 7. Return final_video_url
        pass
```

### MCP Communication Pattern

```python
# src/utils/mcp_client.py

class MCPClient:
    """Generic MCP client for JSON-RPC communication"""
    
    async def call_tool(self, server_name: str, tool_name: str, args: dict) -> dict:
        """Call a tool on an MCP server via JSON-RPC"""
        # 1. Spawn server subprocess if not running
        # 2. Send JSON-RPC request on stdin
        # 3. Read JSON-RPC response on stdout
        # 4. Return result
        pass
```

### Deliverables
- [ ] `src/utils/mcp_client.py` — MCP JSON-RPC client
- [ ] `src/core/orchestrator.py` — Full implementation
- [ ] Integration tests
- [ ] Can run: `uv run src/main.py` and see orchestrator working

### Estimated Effort: 4-6 hours

---

## Phase 4: API Key Integration (MiniMax & FL2V)

### Objective
Integrate real API calls once you have API keys.

### Prerequisites
- MINIMAX_API_KEY environment variable
- FL2V_API_KEY environment variable

### MiniMax Implementation

```python
# mcp_servers/minimax_mcp/minimax_client.py

import aiohttp
from src.config import Settings

class MiniMaxClient:
    def __init__(self, api_key: str, api_base: str = "https://api.minimax.ai"):
        self.api_key = api_key
        self.api_base = api_base
    
    async def voice_clone(self, audio_bytes: bytes, voice_name: str) -> dict:
        """Call MiniMax voice cloning API"""
        # POST to {api_base}/api/voice/clone
        # Return voice_id
        pass
    
    async def text_to_audio(self, text: str, voice_id: str) -> dict:
        """Call MiniMax TTS API"""
        # POST to {api_base}/api/tts
        # Return audio_url
        pass
    
    async def text_to_image(self, prompt: str) -> dict:
        """Call MiniMax image generation"""
        # POST to {api_base}/api/image
        # Return image_url
        pass
```

### FL2V Implementation

```python
# mcp_servers/fl2v_mcp/fl2v_client.py

class FL2VClient:
    async def create_fl2v_task(self, prompt: str, first_frame: str, last_frame: str, ...) -> dict:
        """Submit FL2V generation task"""
        # POST task to FL2V API
        # Return task_id
        pass
    
    async def query_task_status(self, task_id: str) -> dict:
        """Poll task status"""
        # GET task status
        # If completed: download video, upload to S3/Azure, return video_url
        # Otherwise: return status
        pass
```

### Deliverables
- [ ] Set MINIMAX_API_KEY and FL2V_API_KEY in .env
- [ ] MiniMax API client implementation
- [ ] FL2V API client implementation
- [ ] Integration tests with real API
- [ ] Error handling & retries

### Estimated Effort: 3-4 hours per service

---

## Phase 5: OpenAI Agents Setup

### Objective
Implement intelligent planning and decision-making using OpenAI Agents.

### Three Agents

#### 1. Supervisor Agent
```python
# agents/supervisor_agent.py

async def supervisor_agent(story_prompt: str, target_duration_sec: int, segment_len_sec: int):
    """
    Analyze story and create video plan
    
    Input: "A journey through mountains and forests"
    Output: VideoPlan with:
      - segment_count = 10 (for 60s video with 6s segments)
      - segments[].prompt for each segment
      - segments[].narration_text for each segment
      - Continuity rules (smooth transitions)
    """
    # Use OpenAI Agents SDK or Agent Builder
    # Claude or GPT-4 analyzes story
    # Returns structured VideoPlan
    pass
```

#### 2. Frame Designer Agent
```python
# agents/frame_designer_agent.py

async def frame_designer_agent(prev_segment_last_frame: str, current_narration: str):
    """
    Design visual prompt for end-frame image
    
    Input: 
      - Previous segment's last frame (image)
      - Current segment narration text
    
    Output:
      - Visual prompt for end-frame image
      - Optional: generate image via text_to_image()
    """
    # Claude analyzes previous frame and narration
    # Generates detailed visual prompt
    # Optionally calls MiniMax text_to_image()
    pass
```

#### 3. Approval Agent
```python
# agents/approval_agent.py

async def approval_agent(segment_video_url: str, narration_text: str, user_input: str):
    """
    Process user approval decision
    
    User input: "approve" | "regenerate with new prompt" | "edit narration"
    
    Output: Decision + next action
    """
    # Parse user decision
    # Route to orchestrator
    # May trigger regeneration or proceed
    pass
```

### Deliverables
- [ ] OpenAI Agents SDK setup
- [ ] Supervisor Agent implementation
- [ ] Frame Designer Agent implementation
- [ ] Approval Agent implementation
- [ ] Integration with orchestrator
- [ ] HITL gate logic

### Estimated Effort: 6-8 hours

---

## Phase 6: Database & Storage Layer

### Objective
Persistent storage for projects and segments.

### Database Schema

```python
# utils/db.py or models/db.py

class Project(Base):
    project_id: str (PK)
    user_id: str
    story_prompt: str
    status: str  # planning, in_progress, completed, failed
    created_at: datetime
    updated_at: datetime
    video_plan: JSONField  # Full VideoPlan
    final_video_url: Optional[str]

class Segment(Base):
    segment_id: str (PK)
    project_id: str (FK)
    segment_index: int
    prompt: str
    narration_text: str
    first_frame_url: Optional[str]
    last_frame_url: Optional[str]
    video_url: Optional[str]
    audio_url: Optional[str]
    approved: bool
    created_at: datetime
    updated_at: datetime
```

### Storage Options
- Local: `./storage/projects/` (development)
- S3: AWS S3 bucket (production)
- Azure: Azure Blob Storage (production)

### Deliverables
- [ ] SQLAlchemy models
- [ ] Alembic migrations
- [ ] Storage abstraction layer
- [ ] Tests

### Estimated Effort: 2-3 hours

---

## Phase 7: UI/CLI Interface

### Objective
User-facing interface for video creation.

### Options

#### Option A: CLI (Recommended for MVP)
```bash
uv run src/main.py create \
  --story "Once upon a time..." \
  --duration 60 \
  --segment-len 6 \
  --voice sample.wav \
  --start-frame start.jpg

# Shows segment-by-segment progress with approvals
```

#### Option B: Web UI (Flask/FastAPI)
```python
# src/api/app.py

app = FastAPI()

@app.post("/projects")
async def create_project(story: str, duration: int, ...):
    # Create project, start orchestrator
    # Return project_id
    pass

@app.get("/projects/{project_id}/segments/{segment_index}")
async def get_segment(project_id: str, segment_index: int):
    # Return segment preview (video + narration)
    pass

@app.post("/projects/{project_id}/segments/{segment_index}/approve")
async def approve_segment(project_id: str, segment_index: int):
    # Approve segment, proceed to next
    pass
```

### Deliverables
- [ ] CLI interface (Click-based)
- [ ] Or: Flask/FastAPI web interface
- [ ] Job queue for async processing (optional)
- [ ] Tests

### Estimated Effort: 4-6 hours

---

## Total Estimated Effort

| Phase | Hours | Status |
|-------|-------|--------|
| 1: MCP Basics | 6 | ✅ DONE |
| 2: MediaOps MCP | 3 | ⏳ TODO |
| 3: Orchestrator | 5 | ⏳ TODO |
| 4: API Integration | 7 | ⏳ TODO (needs keys) |
| 5: Agents Setup | 7 | ⏳ TODO |
| 6: Database Layer | 3 | ⏳ TODO |
| 7: UI/CLI | 5 | ⏳ TODO |
| **TOTAL** | **36** | |

---

## Decision Tree

### Which phase should I work on next?

1. **Do you have FFmpeg installed?** 
   → Yes: Start Phase 2 (MediaOps MCP)
   → No: Install FFmpeg first

2. **Do you have API keys?**
   → Yes: Can also do Phase 4 alongside Phase 2-3
   → No: Do Phase 2-3 first, then Phase 4

3. **Need approval interface soon?**
   → Yes: Do Phase 7 after Phase 3
   → No: Do Phase 5-6 first

---

## Success Criteria

Each phase is complete when:

- [ ] All code is implemented
- [ ] All functions have docstrings
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Code follows project conventions
- [ ] Documentation is updated

---

For implementation details, see:
- [src/README.md](../src/README.md) — Architecture guide
- [docs/MCP_SETUP.md](MCP_SETUP.md) — MCP specifics
