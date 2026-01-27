# Diagrams MCP Server Setup Guide

## What is Diagrams MCP?

The **Diagrams MCP Server** is an AI-powered tool that generates infrastructure and architecture diagrams directly from Python code. It's perfect for documenting your video_creator project architecture.

### Key Features:
- ✅ **500+ Node Types**: AWS, Azure, GCP, Kubernetes, databases, etc.
- ✅ **Multiple Output Formats**: PNG, PDF, JPG, DOT (importable to draw.io)
- ✅ **Code-as-Diagram**: Define architecture in Python, generate visual diagrams
- ✅ **AI Integration**: Works with Claude/AI assistants for automatic diagram generation
- ✅ **Custom Icons**: Support for company logos and custom icons

---

## Installation Steps

### Prerequisites
- **Python 3.11+** (already have in your project)
- **Graphviz** (system dependency)
- **VS Code** with MCP support
- **uvx** (uv Python tool, auto-installed)

### Step 1: Install Graphviz

**Windows (Recommended: Use Installer)**
1. Download from: https://graphviz.org/download/
2. Run the installer (e.g., `graphviz-12.1.0-win64.exe`)
3. Choose installation path (default is fine)
4. Add to PATH during installation

**Verify Installation:**
```powershell
dot -V
# Output should be: dot - graphviz version X.XX
```

### Step 2: Configure MCP Server in VS Code

**Method 1: Using MCP Settings UI (Easiest)**

1. Open **Command Palette** (`Ctrl+Shift+P`)
2. Type: `MCP: Edit Config File`
3. Add this JSON block:

```json
{
  "mcpServers": {
    "diagrams": {
      "command": "uvx",
      "args": ["diagrams-mcp"]
    }
  }
}
```

4. Save the file
5. Reload VS Code (`Ctrl+Shift+P` → "Developer: Reload Window")

**Method 2: Manual Configuration**

Edit `.vscode/settings.json`:
```json
{
  "mcp.servers": {
    "diagrams": {
      "command": "uvx",
      "args": ["diagrams-mcp"]
    }
  }
}
```

### Step 3: Verify MCP Server is Running

1. Open **Command Palette** (`Ctrl+Shift+P`)
2. Search: `MCP: Servers` or check bottom-right corner of VS Code
3. You should see "diagrams" listed as active

---

## How to Use Diagrams MCP

### Option A: Ask Your AI Assistant

In VS Code with Claude/AI assistant:

```
"Create an architecture diagram for my video_creator project. 
It has:
- Orchestrator in core/orchestrator.py
- Models in models/ (segment.py, video_plan.py)
- Agents in agents/
- MCP Servers for FL2V, MediaOps, and MiniMax
- Storage utilities

Include a PostgreSQL database and Redis cache."
```

The AI will:
1. Analyze your project structure
2. Use the `create_diagram` MCP tool
3. Generate a PNG/PDF diagram
4. Save it to your project

### Option B: Write Code Directly

Create a Python script (example already created):

```python
from diagrams import Diagram, Cluster
from diagrams.programming.language import Python
from diagrams.onprem.database import PostgreSQL

with Diagram("My Architecture", show=False):
    user = Python("User")
    db = PostgreSQL("Database")
    user >> db
```

Run with:
```bash
python create_architecture_diagram.py
```

### Available MCP Tools

| Tool | Purpose |
|------|---------|
| `create_diagram` | Full infrastructure/architecture diagrams with 500+ providers |
| `create_diagram_with_custom_icons` | Use custom company logos or URLs for icons |
| `create_flowchart` | Process flows with 24 shapes (decision points, loops, etc.) |
| `list_available_nodes` | Search all 500+ available node types |
| `validate_diagram_spec` | Test diagram code before generation |

---

## Project Structure for Diagrams

For your **video_creator** project, here's what you can diagram:

```
video_creator/
├── src/
│   ├── main.py              → Entry point
│   ├── config.py            → Configuration service
│   ├── core/
│   │   └── orchestrator.py  → Main orchestration
│   ├── models/              → Data models
│   └── core/                → Business logic
├── agents/                  → AI agents
├── mcp_servers/             
│   ├── fl2v_mcp/            → FL2V video generation
│   ├── mediaops_mcp/        → Media operations
│   └── minimax_mcp/         → MiniMax voice generation
└── storage/                 → Storage abstraction
```

**Sample Diagram Request:**
```
"Show the architecture with:
- Main entry point (src/main.py)
- Orchestrator coordinating all services
- Three MCP servers (FL2V, MediaOps, MiniMax)
- Storage and database layers
- Color code by layer (red=core, blue=agents, green=external)"
```

---

## Importing Diagrams into draw.io

The diagrams generated are PNG/PDF files that can be:

1. **Opened in draw.io**: File → Import → Select PNG/PDF
2. **Used as background reference**: Useful for manual editing
3. **Converted**: PNG → SVG for further editing

**Better Alternative**: Use draw.io's own XML export and keep diagrams-generated images for documentation.

---

## Available Diagram Types

### Infrastructure Diagrams
- AWS (EC2, RDS, Lambda, S3, etc.)
- Azure (VMs, SQL Database, Functions, etc.)
- GCP (Compute Engine, CloudSQL, etc.)
- Kubernetes (Pods, Services, Ingress)
- On-Premise (Servers, Databases)

### Flowcharts
- Process flows with decision points
- CI/CD pipelines
- User workflows

### Custom
- Your own icons from URLs or local files

---

## Troubleshooting

### Issue: "Graphviz not found"
**Solution:** 
- Install Graphviz from https://graphviz.org/download/
- Add to PATH: `C:\Program Files\Graphviz\bin`
- Restart VS Code

### Issue: "uvx command not found"
**Solution:**
- Install uv: `pip install uv`
- Or use `pip install diagrams-mcp` directly

### Issue: MCP Server not showing up in VS Code
**Solution:**
- Restart VS Code completely
- Check `.vscode/settings.json` for correct syntax
- Run `uvx diagrams-mcp` in terminal to verify it runs

---

## Example: Generate Your Project Architecture

**Create file: `diagrams/generate_architecture.py`**

```python
from diagrams import Diagram, Cluster, Edge
from diagrams.programming.language import Python
from diagrams.onprem.queue import Kafka
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.inmemory import Redis
from diagrams.custom import Custom

with Diagram("video_creator_system", show=False, direction="LR", outformat="png"):
    
    with Cluster("User Layer"):
        api = Custom("API/CLI", "./icons/api.png")
    
    with Cluster("Core Application"):
        with Cluster("Orchestration"):
            orchestrator = Python("Orchestrator")
        with Cluster("Models & Logic"):
            models = Python("Models")
            segment = Python("SegmentModel")
            plan = Python("VideoPlan")
    
    with Cluster("Agents"):
        agents = Python("Agents")
    
    with Cluster("MCP Servers"):
        fl2v = Custom("FL2V", "./icons/video.png")
        mediaops = Custom("MediaOps", "./icons/media.png")
        minimax = Custom("MiniMax", "./icons/voice.png")
    
    with Cluster("Data Layer"):
        db = PostgreSQL("PostgreSQL")
        cache = Redis("Redis Cache")
        files = Python("File Storage")
    
    api >> orchestrator
    orchestrator >> [models, segment, plan, agents]
    agents >> [fl2v, mediaops, minimax]
    orchestrator >> [db, cache, files]
```

**To use:**
```bash
cd c:\Users\milan\video_creator
python create_architecture_diagram.py
# Generates: video_creator_system.png
```

---

## Next Steps

1. ✅ Install Graphviz
2. ✅ Configure MCP in VS Code
3. 📝 Generate diagrams for your project
4. 🎨 Import to draw.io for further refinement
5. 📚 Add to documentation/wiki

---

## Resources

- **Diagrams Library**: https://diagrams.mingrammer.com/
- **Diagrams MCP GitHub**: https://github.com/apetta/diagrams-mcp
- **draw.io**: https://draw.io/ (for importing and editing)
- **Smithery MCP Registry**: https://smithery.ai/servers/diagrams-mcp

---

## Questions?

If the MCP server isn't working:
1. Check that Graphviz is installed: `dot -V`
2. Verify uvx works: `uvx --version`
3. Test MCP directly: `uvx diagrams-mcp` in terminal
4. Check VS Code MCP logs: Output → MCP Log

