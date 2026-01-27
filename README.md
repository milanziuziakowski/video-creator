# Video Creator - 1-Minute Video Studio

Build professional 1-minute videos using **MiniMax AI** + **OpenAI Agents** + **MCP Servers**.

## Quick Start

```bash
# Install dependencies
uv sync

# Activate environment
.venv\Scripts\activate  # Windows

# See documentation
cat src/README.md        # Full architecture guide
cat docs/MCP_SETUP.md    # MCP server setup
```

## Project Overview

| Component | Purpose |
|-----------|---------|
| **Orchestrator** | Manages video segment generation workflow |
| **MCP Servers** | Tools for voice cloning, video generation, media processing |
| **OpenAI Agents** | Intelligent planning, frame design, approval workflows |
| **Storage** | S3/Azure for artifacts, SQLite/PostgreSQL for metadata |

### Three MCP Servers

1. **MediaOps MCP** — FFmpeg operations (extract frames, concat video/audio, mux)
2. **MiniMax MCP** — Voice cloning, TTS, image/video generation
3. **FL2V MCP** — First-Last Frame video generation (seamless segment transitions)

## Architecture

```
User Input (story, voice, duration)
    ↓
[Supervisor Agent] → Creates VideoPlan (segments, prompts, narration)
    ↓
[Voice Cloning] → Gets voice_id
    ↓
For each segment:
    ├─ [Frame Designer] → Generates end-frame prompt
    ├─ [FL2V MCP] → Video (first_frame + last_frame)
    ├─ [MiniMax MCP] → Audio (cloned voice TTS)
    └─ [HITL Gate] → User approves / regenerates
    ↓
[MediaOps MCP] → Concat videos + audios → Mux → Final video
    ↓
Final 1-minute video (≤60s, segment-controlled, human-approved)
```

## Development Status

✅ **Complete:**
- Project structure & scaffolding
- Data models (VideoPlan, Segment)
- MCP server skeletons
- Configuration management
- Documentation

⏳ **TODO:**
- MediaOps MCP (FFmpeg implementation)
- Orchestrator integration
- MiniMax/FL2V API integration (requires API keys)
- OpenAI Agents setup
- Database layer
- UI/CLI interface

## Documentation

- **[src/README.md](src/README.md)** — Comprehensive architecture & development guide
- **[docs/MCP_SETUP.md](docs/MCP_SETUP.md)** — MCP server setup, testing, debugging
- **[docs/PROJECT_SETUP_COMPLETE.md](docs/PROJECT_SETUP_COMPLETE.md)** — Setup summary & next steps
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — Original system design document

## Key Constraints

- `target_duration_sec ≤ 60` seconds
- `segment_len_sec ∈ {6, 10}` seconds
- Per-segment human approval (HITL)
- Deterministic media ops (FFmpeg, not LLM)
- Audio/video alignment guaranteed via ffmpeg mux

## Getting Started

1. **Set up environment:**
   ```bash
   uv sync
   .venv\Scripts\activate
   ```

2. **Review architecture:**
   - Read [src/README.md](src/README.md) for full overview
   - Check [docs/MCP_SETUP.md](docs/MCP_SETUP.md) for MCP details

3. **Start implementing:**
   - First: MediaOps MCP (FFmpeg wrapper) — no external APIs needed
   - Then: Orchestrator integration
   - Finally: Agent setup + API integrations

## Environment Setup

Copy `.env.example` to `.env` and fill in:

```bash
cp .env.example .env
```

Required when ready:
- `OPENAI_API_KEY` — For agents
- `MINIMAX_API_KEY` — For voice/video generation
- `FL2V_API_KEY` — For segment video generation

## Commands

```bash
# Test MCP server (MediaOps - no API key needed)
cd mcp_servers/mediaops_mcp
uv run mediaops_server.py

# Run tests
pytest tests/ -v

# Start application (when fully implemented)
uv run src/main.py
```

## References

- **MCP Docs:** https://modelcontextprotocol.io/
- **OpenAI Agents:** https://platform.openai.com/docs/agents
- **FFmpeg:** https://ffmpeg.org/

---

For detailed implementation guide, see [src/README.md](src/README.md).
