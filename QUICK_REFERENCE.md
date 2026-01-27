# Quick Reference Card

## Essential Files

| File | Purpose | Priority |
|------|---------|----------|
| [src/README.md](src/README.md) | **Complete dev guide** | 🔴 READ FIRST |
| [docs/MCP_SETUP.md](docs/MCP_SETUP.md) | MCP server details | 🟡 Second |
| [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) | Implementation phases | 🟡 Second |
| [GETTING_STARTED.md](GETTING_STARTED.md) | Quick start guide | 🟡 Second |
| [README.md](README.md) | Project overview | 🟢 Reference |

## File Structure Cheat Sheet

```
src/
  ├── main.py              → Entry point
  ├── config.py            → Settings from .env
  ├── models/
  │   ├── segment.py       → Segment schema
  │   └── video_plan.py    → VideoPlan schema
  └── core/
      └── orchestrator.py  → Main workflow

mcp_servers/
  ├── minimax_mcp/
  │   └── minimax_server.py    → Voice/video/image tools
  ├── mediaops_mcp/
  │   └── mediaops_server.py   → FFmpeg tools
  └── fl2v_mcp/
      └── fl2v_server.py       → Segment video tools

agents/                     → OpenAI Agent implementations
utils/                      → Helpers (logger, storage, db, validators)
tests/                      → Unit & integration tests
docs/                       → Detailed guides
```

## Key Commands

```bash
# Setup
uv sync                              # Install deps
.venv\Scripts\activate               # Activate env

# Test MCP server (no API keys needed)
cd mcp_servers/mediaops_mcp
uv run mediaops_server.py

# Run application (when implemented)
uv run src/main.py

# Run tests (when implemented)
pytest tests/ -v
```

## Architecture Overview

```
User Story → Supervisor Agent → VideoPlan (segments + prompts + narration)
                                ↓
                          Voice Clone (MiniMax)
                                ↓
                        For Each Segment:
                    ┌─────────┬─────────┐
                    ↓         ↓         ↓
              Frame Design  FL2V Video  TTS Audio
                    ↓         ↓         ↓
                    └─────────┼─────────┘
                              ↓
                          HITL Gate (User Approves)
                              ↓
                    MediaOps: Concat + Mux
                              ↓
                        Final 1-Min Video
```

## Development Phases

| Phase | Task | Status | Effort |
|-------|------|--------|--------|
| 1 | MCP Basics & Skeleton | ✅ Done | 6h |
| 2 | MediaOps MCP (FFmpeg) | ⏳ TODO | 3h |
| 3 | Orchestrator Integration | ⏳ TODO | 5h |
| 4 | API Integration (Keys) | ⏳ TODO | 7h |
| 5 | OpenAI Agents | ⏳ TODO | 7h |
| 6 | Database Layer | ⏳ TODO | 3h |
| 7 | UI/CLI Interface | ⏳ TODO | 5h |

**Start with Phase 2** (no API keys needed)

## Data Models

### VideoPlan
```python
{
  "project_id": "proj_123",
  "target_duration_sec": 60,
  "segment_len_sec": 6,
  "segment_count": 10,
  "voice_id": "voice_xyz",
  "segments": [
    {
      "segment_index": 0,
      "prompt": "A beautiful sunset...",
      "narration_text": "Once upon a time...",
      "approved": false
    }
    # ... 9 more segments
  ],
  "final_video_url": null
}
```

## MCP Tool Categories

### MediaOps (FFmpeg) - No Keys
- `extract_last_frame(video) → image`
- `concat_videos(videos[]) → video`
- `concat_audios(audios[]) → audio`
- `mux_audio_video(video, audio) → final_video`
- `normalize_audio(audio) → audio`
- `probe_duration(media) → duration_sec`

### MiniMax - Needs Key
- `voice_clone(audio, name) → voice_id`
- `text_to_audio(text, voice_id) → audio_url`
- `text_to_image(prompt) → image_url`
- `generate_video(prompt, first_frame, last_frame) → video_url`
- `query_video_generation(task_id) → status, video_url`

### FL2V - Needs Key
- `create_fl2v_task(prompt, first_frame, last_frame) → task_id`
- `query_task_status(task_id) → status, video_url`

## Environment Setup

```bash
# Copy template
cp .env.example .env

# Fill in (when ready)
OPENAI_API_KEY=sk-xxx              # For agents
MINIMAX_API_KEY=xxx                # For voice/video/image
FL2V_API_KEY=xxx                   # For segment videos
STORAGE_TYPE=local                 # or s3, azure
DB_TYPE=sqlite                     # or postgresql
```

## Testing Patterns

```python
# Test MCP tool
async def test_extract_last_frame():
    result = await extract_last_frame("test.mp4", "output.jpg")
    assert result["output_path"] == "output.jpg"
    assert Path(result["output_path"]).exists()

# Test orchestrator
async def test_process_segment():
    orch = VideoOrchestrator(settings)
    result = await orch.process_segment(...)
    assert result["status"] == "approved"
```

## Common Patterns

### Adding a tool to MCP server
```python
@mcp.tool()
async def my_tool(param: str) -> dict:
    """Docstring (auto-generated as tool description)"""
    logger.info(f"Tool called: {param}")
    # Implementation
    return {"result": "value"}
```

### Creating a pydantic model
```python
class MyModel(BaseModel):
    field1: str = Field(..., description="Description")
    field2: Optional[int] = None
    
    class Config:
        json_schema_extra = {"example": {...}}
```

### Calling MCP tool from orchestrator
```python
# (Will be implemented in Phase 3)
result = await mcp_client.call_tool("server_name", "tool_name", {"param": value})
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `mcp.server not found` | Run `uv sync` to install mcp package |
| MCP server won't start | Check stderr for errors (logs go there, not stdout) |
| Import errors | Check PYTHONPATH, try `uv run` instead of `python` |
| API key not loaded | Verify in `.env` file, check `Settings` class loads it |
| FFmpeg not found | Install FFmpeg, add to PATH |

## Next Steps

1. ✅ **Read** [src/README.md](src/README.md)
2. ⏳ **Run** `uv sync` to install deps
3. ⏳ **Implement** Phase 2 (MediaOps MCP)
4. ⏳ **Test** with sample video

**Estimated time to Phase 2 completion: 3 hours**

---

For details, see [src/README.md](src/README.md) or [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)
