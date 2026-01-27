# Video Creator Application - File Architecture & Development Guide

## Overview
This is a 1-minute video studio powered by MiniMax + OpenAI Agents. The application orchestrates video segment generation with human-in-the-loop approvals using MCP (Model Context Protocol) servers.

## Project Structure

```
video_creator/
├── ARCHITECTURE.md                 # System design document
├── pyproject.toml                  # Python project config (UV package manager)
├── README.md                       # Project setup instructions
├── .env.example                    # Environment variables template
│
├── src/                            # Main application code
│   ├── __init__.py
│   ├── main.py                     # Entry point (CLI/API)
│   ├── config.py                   # Configuration management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── video_plan.py           # VideoPlan dataclass (segments, prompts, narration)
│   │   ├── segment.py              # Segment state & metadata
│   │   └── project.py              # Project state schema
│   │
│   └── core/
│       ├── __init__.py
│       ├── orchestrator.py         # Main orchestration logic
│       ├── hitl_manager.py         # Human-in-the-loop gate
│       └── approval_workflow.py    # Approval/regenerate logic
│
├── mcp_servers/                    # MCP Server implementations
│   │
│   ├── minimax_mcp/                # MiniMax API wrapper (FastMCP)
│   │   ├── __init__.py
│   │   ├── minimax_server.py       # FastMCP server instance
│   │   ├── tools/
│   │   └── config.py               # MiniMax API config (placeholder for API key)
│   │
│   ├── mediaops_mcp/               # FFmpeg + Media Operations (FastMCP)
│   │   ├── __init__.py
│   │   ├── mediaops_server.py      # FastMCP server instance
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── extract_frame.py    # extract_last_frame(video) -> image
│   │   │   ├── concat_videos.py    # concat_videos(videos[]) -> video
│   │   │   ├── concat_audios.py    # concat_audios(audios[]) -> audio
│   │   │   ├── mux_audio_video.py  # mux_audio_video(video, audio) -> final_video
│   │   │   ├── normalize_audio.py  # normalize_audio(audio) -> normalized_audio
│   │   │   └── probe_duration.py   # probe_duration(media) -> duration_sec
│   │   ├── ffmpeg_wrapper.py       # FFmpeg command execution wrapper
│   │   └── validators.py           # Media file validators
│   │
│   └── fl2v_mcp/                   # First-Last Frame Video Generator (FastMCP)
│       ├── __init__.py
│       ├── fl2v_server.py          # FastMCP server instance
│       ├── tools/
│       │   ├── __init__.py
│       │   └── create_fl2v_task.py # create_fl2v_task(prompt, first_frame, last_frame, model, duration, resolution)
│       └── fl2v_client.py          # FL2V API client wrapper
│
├── agents/                         # OpenAI Agents (Agent Builder / SDK)
│   ├── __init__.py
│   ├── supervisor_agent.py         # Director Agent: builds VideoPlan
│   ├── frame_designer_agent.py     # Frame Designer: generates end-frame prompts
│   ├── approval_agent.py           # Approval workflow handler
│   └── agent_tools.py              # Tool definitions for agents
│
├── utils/                          # Utility modules
│   ├── __init__.py
│   ├── logger.py                   # Logging configuration (write to stderr)
│   ├── storage.py                  # S3/Azure Blob Storage abstraction
│   ├── db.py                       # Database layer (project metadata, segment statuses)
│   ├── validators.py               # Input validation (audio, images, prompts)
│   ├── exceptions.py               # Custom exceptions
│   └── constants.py                # Application constants
│
├── storage/                        # Local storage for artifacts (during dev)
│   ├── projects/                   # Project folders
│   ├── temp/                       # Temporary working files
│   └── .gitkeep
│
├── tests/                          # Unit & integration tests
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures
│   ├── test_models.py              # Videoplan, Segment, Project schemas
│   ├── test_orchestrator.py        # Orchestration logic
│   ├── test_mcp_servers.py         # MCP server tool execution
│   └── test_approval_workflow.py   # HITL gate & approval logic
│
└── docs/                           # Additional documentation
    ├── MCP_SETUP.md                # MCP server configuration guide
    ├── AGENT_SETUP.md              # OpenAI Agents setup & examples
    ├── API_REFERENCE.md            # API endpoint documentation
    └── DEPLOYMENT.md               # Deployment instructions
```

---

## Core Concepts

### 1. **Data Models** (`src/models/`)

#### VideoPlan
```python
# Example structure
{
    "project_id": "proj_12345",
    "target_duration_sec": 60,
    "segment_len_sec": 6,
    "segment_count": 10,
    "voice_id": "voice_xyz",
    "segments": [
        {
            "segment_index": 0,
            "prompt": "A beautiful sunset over mountains...",
            "narration_text": "Narrated audio text...",
            "first_frame_image_url": "./storage/projects/proj_12345/segment_0_first_frame.jpg",
            "last_frame_image_url": "./storage/projects/proj_12345/segment_0_last_frame.jpg",
            "video_task_id": "task_123",
            "segment_video_url": "./storage/projects/proj_12345/segment_0_video.mp4",
            "segment_audio_url": "./storage/projects/proj_12345/segment_0_audio.mp3",
            "approved": False
        },
        # ... more segments
    ],
    "assembled_video_url": "./storage/projects/proj_12345/assembled_video.mp4",
    "assembled_audio_url": "./storage/projects/proj_12345/assembled_audio.mp3",
    "final_video_url": "./storage/projects/proj_12345/final_video.mp4"
}
```

### 2. **MCP Servers** (`mcp_servers/`)

Each MCP server follows the **FastMCP** pattern from official MCP documentation:
- Uses Python type hints for automatic tool definition generation
- Writes logs to stderr (never stdout, which breaks JSON-RPC)
- Runs via `uv run` command
- Exposes `@mcp.tool()` decorated async functions

**MiniMax MCP** — Third-party tools (voice cloning, TTS, video generation, image generation)

**MediaOps MCP** — Deterministic FFmpeg operations (no LLM involvement)

**FL2V MCP** — First-Last Frame video generation wrapper

### 3. **Orchestration** (`src/core/`)

- **Orchestrator**: Manages the full runtime flow
  - Creates VideoPlan from user inputs (story prompt, voice sample, duration, segment length)
  - Clones voice → obtains voice_id
  - Loops through segments (segment_index 0 to segment_count-1)
  - Extracts last frame from previous segment's video (if i > 0)
  - Generates end-frame image for current segment
  - Calls FL2V MCP to generate segment video
  - Calls MiniMax MCP to generate segment audio
  - Passes to HITL gate

- **HITL Manager**: Human approval gate
  - Blocks until user approves segment (or regenerates with new prompt)
  - Updates segment state in database
  - Appends approved segment to assembled tracks

- **Approval Workflow**: Handles user actions
  - `approve_segment()` → marks segment as approved, proceeds
  - `regenerate_segment(new_prompt)` → updates prompt, re-runs segment generation
  - `edit_segment(updated_narration)` → updates narration, regenerates audio

### 4. **Agent Framework** (`agents/`)

**Supervisor Agent** — Uses OpenAI Agent SDK to:
- Analyze user story prompt
- Plan segment breakdowns (what happens in each 6s/10s segment)
- Generate narration text for each segment
- Generate end-frame image prompts for continuity

**Frame Designer Agent** — Uses OpenAI Agent SDK to:
- Receive segment context (previous segment's last frame, current narration)
- Generate visual prompt for end-frame image
- Optionally call MiniMax text_to_image() to generate the image

**Approval Agent** — Handles user interaction:
- Presents segment preview (video + narration)
- Collects user decision (approve / regenerate / edit)
- Routes decision to orchestrator

---

## Development Workflow

### Step 1: Environment Setup

```bash
# Install UV package manager (if not already done)
# See: https://docs.astral.sh/uv/

# Create virtual environment
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies (from pyproject.toml)
uv sync
```

### Step 2: Configure Environment Variables

```bash
# Copy template and fill in values
cp .env.example .env

# Required variables:
# MINIMAX_API_KEY=xxxx         (add when ready)
# OPENAI_API_KEY=sk-xxx        (for Agents)
# STORAGE_TYPE=local|s3|azure  (local during dev)
# DB_TYPE=postgres              (postgres during dev)
```

### Step 3: Implement MCP Servers

Each MCP server is implemented as a standalone Python module:

**MiniMax MCP** (placeholder — will use official MiniMax Python SDK)
```python
# mcp_servers/minimax_mcp/minimax_server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("minimax")

@mcp.tool()
async def voice_clone(audio_bytes: bytes, voice_name: str) -> dict:
    """Clone a voice from audio sample and return voice_id."""
    # Placeholder: call MiniMax API when ready
    pass

# ... other tools

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
```

**MediaOps MCP** (FFmpeg wrapper)
```python
# mcp_servers/mediaops_mcp/mediaops_server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mediaops")

@mcp.tool()
async def extract_last_frame(video_path: str) -> str:
    """Extract last frame from video and return image path."""
    # Use ffmpeg to extract frame
    pass

# ... other tools

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
```

**FL2V MCP** (First-Last Frame video generation)
```python
# mcp_servers/fl2v_mcp/fl2v_server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("fl2v")

@mcp.tool()
async def create_fl2v_task(prompt: str, first_frame: str, last_frame: str, 
                           model: str, duration: int, resolution: str) -> dict:
    """Create FL2V video generation task and return task_id."""
    # Call FL2V API
    pass

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
```

### Step 4: Register MCP Servers with VS Code / Claude for Desktop

Create `claude_desktop_config.json` (macOS/Linux: `~/Library/Application Support/Claude/`, Windows: `%APPDATA%\Claude\`) or VS Code settings:

```json
{
  "mcpServers": {
    "minimax": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/video_creator/mcp_servers/minimax_mcp",
        "run",
        "minimax_server.py"
      ]
    },
    "mediaops": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/video_creator/mcp_servers/mediaops_mcp",
        "run",
        "mediaops_server.py"
      ]
    },
    "fl2v": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/video_creator/mcp_servers/fl2v_mcp",
        "run",
        "fl2v_server.py"
      ]
    }
  }
}
```

### Step 5: Implement Core Models & Orchestration

1. Define data models in `src/models/` (VideoPlan, Segment, Project)
2. Implement orchestrator in `src/core/orchestrator.py`
3. Implement HITL manager in `src/core/hitl_manager.py`
4. Create API/CLI entry point in `src/main.py`

### Step 6: Integrate with OpenAI Agents

Use OpenAI Agent Builder or Agents SDK to:
- Create Supervisor Agent for VideoPlan generation
- Create Frame Designer Agent for end-frame prompts
- Create Approval Agent for user interaction

### Step 7: Testing & Validation

Run tests:
```bash
pytest tests/ -v
```

---

## Runtime Flow (Happy Path)

1. **User Input**
   - Uploads start frame image, voice sample audio, story prompt
   - Sets target duration (≤60s) and segment length (6s or 10s)

2. **Plan Generation**
   - Supervisor Agent analyzes inputs → creates VideoPlan JSON
   - Voice cloning: MiniMax TTS to get voice_id

3. **Segment Loop** (for each segment i from 0 to segment_count-1)
   - Extract first_frame (start_frame if i=0, else last_frame of prev segment)
   - Frame Designer Agent generates end_frame_prompt
   - Generate end_frame_image via MiniMax text_to_image()
   - Call FL2V MCP → create_fl2v_task() → get video_task_id
   - Call MiniMax MCP → text_to_audio() → get segment_audio_url
   - **HITL Gate**: Present segment to user
     - If approved: proceed to next segment
     - If regenerate: update prompt, restart segment generation
     - If edit: update narration, regenerate audio, stay at HITL gate

4. **Finalization**
   - MediaOps MCP: concat_videos(all_segment_videos) → assembled_video
   - MediaOps MCP: concat_audios(all_segment_audios) → assembled_audio
   - MediaOps MCP: mux_audio_video(assembled_video, assembled_audio) → final_video
   - Return final_video URL to user

---

## Key Files to Implement (Priority Order)

1. **src/models/** — VideoPlan, Segment, Project dataclasses
2. **src/core/orchestrator.py** — Main orchestration logic
3. **mcp_servers/mediaops_mcp/** — FFmpeg wrapper (deterministic, no API keys needed)
4. **mcp_servers/minimax_mcp/** — API wrapper skeleton (ready for API key)
5. **mcp_servers/fl2v_mcp/** — FL2V API wrapper skeleton
6. **agents/supervisor_agent.py** — Plan generator
7. **src/main.py** — CLI/API entry point
8. **tests/** — Unit & integration tests

---

## Next Steps

1. ✅ Research MCP architecture → **DONE**
2. ⏳ Set up MediaOps MCP (FFmpeg wrapper) — *no external dependencies*
3. ⏳ Implement core models & orchestrator
4. ⏳ Set up MiniMax MCP structure (ready for API key integration)
5. ⏳ Implement OpenAI Agents for planning & approvals
6. ⏳ Create UI/CLI for user interaction
7. ⏳ Integration testing & deployment

---

## References

- **MCP Official Docs**: https://modelcontextprotocol.io/
- **MCP Build Server Guide**: https://modelcontextprotocol.io/docs/develop/build-server
- **FastMCP (Python)**: https://github.com/modelcontextprotocol/python-sdk
- **OpenAI Agent Builder**: https://platform.openai.com/docs/agents
- **FFmpeg Documentation**: https://ffmpeg.org/documentation.html
