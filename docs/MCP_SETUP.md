# MCP Server Setup & Configuration Guide

## Overview

Your project uses **Model Context Protocol (MCP)** with three independent MCP servers that can be tested and developed separately:

1. **MiniMax MCP** — API wrapper for voice cloning, TTS, video/image generation
2. **MediaOps MCP** — FFmpeg-based deterministic media operations
3. **FL2V MCP** — First-Last Frame video generation wrapper

## MCP Architecture (from official docs)

**Key Points:**
- MCP servers use **JSON-RPC over stdio** (STDOUT/STDIN pipes)
- FastMCP (Python SDK) automatically generates tool definitions from type-hinted async functions
- Logging must write to **stderr** (never stdout, which breaks JSON-RPC)
- MCP servers are language-agnostic and can be written in Python, TypeScript, Go, etc.

## Testing Individual MCP Servers

### Prerequisites

```bash
# Install dependencies from pyproject.toml
cd c:\Users\milan\video_creator
uv sync
```

### Test MediaOps MCP (Recommended First)

MediaOps is the simplest to test because it doesn't require external API keys:

```bash
# Terminal 1: Start MCP server
cd c:\Users\milan\video_creator\mcp_servers\mediaops_mcp
uv run mediaops_server.py

# Output should show it's listening on stdio
# Example: "Starting MediaOps MCP Server"
```

The server is now ready to receive JSON-RPC requests. In a real environment (Claude for Desktop or VS Code), the client would pipe JSON-RPC messages to it.

### Test MiniMax MCP

```bash
cd c:\Users\milan\video_creator\mcp_servers\minimax_mcp
uv run minimax_server.py

# This will wait for API key integration
```

### Test FL2V MCP

```bash
cd c:\Users\milan\video_creator\mcp_servers\fl2v_mcp
uv run fl2v_server.py

# This will wait for API key integration
```

## Registering MCP Servers with Claude for Desktop

**Note:** Claude for Desktop is macOS-only. For Windows, you can use VS Code or build a custom client.

### macOS Setup

1. Create/edit `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mediaops": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/YOUR_USERNAME/path/to/video_creator/mcp_servers/mediaops_mcp",
        "run",
        "mediaops_server.py"
      ]
    },
    "minimax": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/YOUR_USERNAME/path/to/video_creator/mcp_servers/minimax_mcp",
        "run",
        "minimax_server.py"
      ]
    },
    "fl2v": {
      "command": "uv",
      "args": [
        "/Users/YOUR_USERNAME/path/to/video_creator/mcp_servers/fl2v_mcp",
        "run",
        "fl2v_server.py"
      ]
    }
  }
}
```

2. Restart Claude for Desktop
3. Click the "+" icon in Claude → "Connectors" → should see your MCP servers listed

## Registering MCP Servers with VS Code

VS Code support for MCP is still emerging. Check the [MCP documentation](https://modelcontextprotocol.io/) for the latest VS Code integration.

## Windows-Specific Notes

On Windows, you have these options:

1. **Build your own MCP client** (using the MCP Python SDK)
2. **Use WSL (Windows Subsystem for Linux)** to run Claude for Desktop
3. **Implement a custom orchestrator** that calls MCP servers directly via subprocess

For development, we recommend **Option 3**: implementing a custom Python orchestrator that spawns MCP servers and communicates with them via JSON-RPC over subprocess pipes.

## Implementation Checklist

### Phase 1: MCP Server Basics ✅ DONE
- [x] Research MCP documentation
- [x] Create FastMCP server skeletons
- [x] Define tool signatures (type-hinted async functions)
- [x] Set up logging to stderr

### Phase 2: MediaOps MCP (No External Dependencies)
- [ ] Implement FFmpeg wrapper functions
- [ ] Test extract_last_frame with sample video
- [ ] Test concat_videos
- [ ] Test mux_audio_video
- [ ] Test probe_duration
- [ ] Create unit tests

### Phase 3: MiniMax MCP (Requires API Key)
- [ ] Add MINIMAX_API_KEY to .env
- [ ] Implement voice_clone tool
- [ ] Implement text_to_audio tool
- [ ] Implement text_to_image tool
- [ ] Add error handling for API failures
- [ ] Create integration tests

### Phase 4: FL2V MCP (Requires API Key)
- [ ] Add FL2V_API_KEY to .env
- [ ] Implement create_fl2v_task tool
- [ ] Implement query_task_status tool
- [ ] Add polling logic
- [ ] Create integration tests

### Phase 5: Orchestrator & Agents
- [ ] Implement src/core/orchestrator.py
- [ ] Integrate MCP clients
- [ ] Implement agents (Supervisor, Frame Designer)
- [ ] Add HITL gate logic
- [ ] Create end-to-end tests

## API Key Integration Pattern

When you're ready to add API keys, follow this pattern:

```python
# mcp_servers/minimax_mcp/config.py
import os
from pydantic import Field
from pydantic_settings import BaseSettings

class MiniMaxConfig(BaseSettings):
    api_key: str = Field(..., alias="minimax_api_key")
    api_base_url: str = "https://api.minimax.ai"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# In minimax_server.py
config = MiniMaxConfig()

@mcp.tool()
async def voice_clone(audio_bytes: bytes, voice_name: str) -> dict:
    # Now you can use config.api_key
    response = await call_minimax_api(config.api_key, ...)
    return {...}
```

## Running the Full Application

Once all MCP servers and agents are implemented:

```bash
# Start orchestrator (which manages MCP servers internally)
cd c:\Users\milan\video_creator
uv run src/main.py

# Or with CLI arguments
uv run src/main.py --story "Once upon a time..." --duration 60 --segment-len 6
```

## Debugging MCP Servers

MCP servers communicate via JSON-RPC over stdio. To debug:

1. **Check stderr for logs** — MCP servers write logs to stderr
2. **Monitor JSON-RPC messages** — Capture stdin/stdout to see JSON-RPC traffic
3. **Use mcp-cli (if available)** — Official CLI tool for testing MCP servers

Example debug output:
```
{"jsonrpc": "2.0", "method": "initialize", "params": {...}, "id": 1}
{"jsonrpc": "2.0", "result": {...}, "id": 1}
```

## References

- [MCP Quickstart](https://modelcontextprotocol.io/quickstart)
- [MCP Build Server Guide](https://modelcontextprotocol.io/docs/develop/build-server)
- [Python MCP SDK GitHub](https://github.com/modelcontextprotocol/python-sdk)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [FFmpeg Documentation](https://ffmpeg.org/)
