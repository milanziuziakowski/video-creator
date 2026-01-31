# AI Video Creator - GitHub Copilot Instructions

This file provides context and instructions for GitHub Copilot when working on this project.

---

## Project Overview

**AI Video Creator** is a web application for generating 1-minute AI videos using:
- **Frontend:** React 18+ with TypeScript, Tailwind CSS, MSAL (Azure Entra ID)
- **Backend:** Python 3.11+, FastAPI, OpenAI Agents SDK, SQLAlchemy
- **External APIs:** MiniMax (video generation, voice cloning, TTS), OpenAI (planning)
- **Infrastructure:** Azure App Service, Azure Static Web Apps, PostgreSQL

### Key Architecture Principles

1. **No MCP Servers** - Use direct API calls to MiniMax and OpenAI
2. **Human-in-the-Loop (HITL)** - Users review and approve AI-generated content
3. **Monolithic Backend** - Single FastAPI application, no microservices
4. **SOLID Principles** - Clean separation of concerns, dependency injection

---

## Directory Structure

```
ai-video-creator/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Pydantic settings
│   │   ├── api/
│   │   │   ├── deps.py          # FastAPI dependencies
│   │   │   └── v1/
│   │   │       ├── projects.py  # Project CRUD endpoints
│   │   │       ├── segments.py  # Segment endpoints
│   │   │       └── generation.py # Generation endpoints
│   │   ├── agents/
│   │   │   └── supervisor_agent.py # OpenAI Agents SDK
│   │   ├── auth/
│   │   │   └── azure_auth.py    # Token validation
│   │   ├── db/
│   │   │   ├── models/          # SQLAlchemy models
│   │   │   └── session.py       # Database session
│   │   ├── integrations/
│   │   │   └── minimax_client.py # Direct MiniMax API
│   │   ├── models/              # Pydantic schemas
│   │   └── services/            # Business logic
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── api/                 # API client & hooks
│   │   ├── auth/                # MSAL configuration
│   │   ├── components/          # React components
│   │   ├── pages/               # Page components
│   │   └── types/               # TypeScript types
│   └── e2e/                     # Playwright tests
└── implementation-plan/         # Documentation
```

---

## Coding Standards

### Python (Backend)

```python
# Use type hints everywhere
async def create_project(
    user_id: str,
    data: ProjectCreate,
    db: AsyncSession,
) -> Project:
    """Create a new project.
    
    Args:
        user_id: The authenticated user's ID
        data: Project creation data
        db: Database session
        
    Returns:
        Created project
        
    Raises:
        ValueError: If project name is empty
    """
    pass

# Use Pydantic for validation
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    story_prompt: Optional[str] = None
    target_duration_sec: int = Field(60, ge=6, le=60)

# Use async/await for I/O operations
async def generate_video(prompt: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(...)
    return response.json()["task_id"]

# Dependencies via FastAPI Depends
@router.post("/projects")
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = ProjectService(db)
    return await service.create_project(user.id, data)
```

### TypeScript (Frontend)

```typescript
// Use functional components with hooks
export function ProjectCard({ project }: ProjectCardProps) {
  const [isLoading, setIsLoading] = useState(false);
  
  const handleClick = useCallback(() => {
    // ...
  }, []);
  
  return (
    <div className="...">
      {/* ... */}
    </div>
  );
}

// Use React Query for data fetching
export function useProject(projectId: string) {
  return useQuery({
    queryKey: ["projects", projectId],
    queryFn: async () => {
      const { data } = await apiClient.get<Project>(`/projects/${projectId}`);
      return data;
    },
    enabled: !!projectId,
  });
}

// Use explicit types, avoid 'any'
interface Segment {
  id: string;
  index: number;
  videoPrompt: string;
  status: SegmentStatus;
}

// Use Tailwind for styling (no separate CSS files)
<button className="rounded-lg bg-primary-600 px-4 py-2 text-white hover:bg-primary-700">
  Submit
</button>
```

---

## MiniMax API Integration

When working with MiniMax API, follow these patterns:

### Video Generation

```python
# Start generation task
async def generate_video(
    prompt: str,
    first_frame: str,
    last_frame: Optional[str] = None,
) -> str:
    """Start video generation and return task_id."""
    payload = {
        "prompt": prompt,
        "first_frame_image": first_frame,
        "model": "MiniMax-Hailuo-02",
        "duration": 6,  # or 10
        "resolution": "720P",
    }
    if last_frame:
        payload["last_frame_image"] = last_frame
    
    response = await client.post(
        "https://api.minimax.io/v1/video_generation",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json=payload,
    )
    return response.json()["task_id"]

# Poll for completion
async def poll_video_status(task_id: str) -> dict:
    """Poll until video is ready or failed."""
    while True:
        response = await client.get(
            "https://api.minimax.io/v1/query/video_generation",
            params={"task_id": task_id},
        )
        data = response.json()
        
        if data["status"] == "Success":
            return {"file_id": data["file_id"], "status": "complete"}
        elif data["status"] == "Fail":
            raise Exception("Video generation failed")
        
        await asyncio.sleep(10)  # Poll every 10 seconds
```

### Voice Cloning

```python
# Upload audio file
file_id = await upload_file(audio_bytes, "sample.mp3", "voice_clone")

# Clone voice
voice_id = await clone_voice(file_id, "custom-voice-id")

# Generate speech
audio = await text_to_audio(text, voice_id)
```

---

## OpenAI Agents SDK Integration

Use structured outputs for AI planning:

```python
from agents import Agent, function_tool, Runner
from pydantic import BaseModel

class VideoStoryPlan(BaseModel):
    title: str
    segments: List[SegmentPrompt]

# Create agent with tools
supervisor_agent = Agent(
    name="Video Story Supervisor",
    instructions="...",
    tools=[create_video_plan],
    model="gpt-4o",
)

# Run agent
result = await Runner.run(supervisor_agent, user_message)
plan = result.final_output_as(VideoStoryPlan)
```

---

## Testing Patterns

### Backend Tests

```python
@pytest.mark.asyncio
async def test_create_project(client: AsyncClient, mock_user: User):
    response = await client.post(
        "/api/v1/projects/",
        json={"name": "Test", "targetDurationSec": 30},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test"

# Mock external APIs
@respx.mock
async def test_voice_clone(client: AsyncClient):
    respx.post("https://api.minimax.io/v1/voice_clone").mock(
        return_value=httpx.Response(200, json={"voice_id": "test"})
    )
    # ... test code
```

### Frontend E2E Tests

```typescript
test("should create project", async ({ page }) => {
  await page.goto("/projects/new");
  await page.fill('[data-testid="project-name"]', "Test");
  await page.click('[data-testid="create-button"]');
  await expect(page).toHaveURL(/\/projects\/[a-z0-9-]+$/);
});
```

---

## Common Tasks

### Adding a New API Endpoint

1. Create Pydantic schemas in `app/models/`
2. Add business logic in `app/services/`
3. Create route in `app/api/v1/`
4. Add dependency injection for auth and DB
5. Write tests in `tests/`

### Adding a New React Component

1. Create component in `src/components/`
2. Use TypeScript interfaces for props
3. Use Tailwind for styling
4. Add data-testid for E2E tests
5. Create hook if needed in `src/api/hooks/`

### Adding a New Database Model

1. Create SQLAlchemy model in `app/db/models/`
2. Create Alembic migration: `alembic revision --autogenerate`
3. Create Pydantic schemas for API
4. Update service layer

---

## Do NOT Do

- ❌ Create MCP servers - use direct API calls
- ❌ Use class components in React - use functional components
- ❌ Use `any` type in TypeScript - be explicit
- ❌ Store secrets in code - use environment variables
- ❌ Skip error handling - always handle API failures gracefully
- ❌ Write CSS files - use Tailwind utility classes
- ❌ Use synchronous I/O in async contexts - always await

---

## References

- [Implementation Plan](./implementation-plan/) - Detailed implementation guides
- [MiniMax API Docs](https://www.minimax.io/docs) - Video generation API
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) - Agent framework
- [FastAPI Docs](https://fastapi.tiangolo.com/) - Backend framework
- [React Query](https://tanstack.com/query) - Data fetching
- [MSAL React](https://github.com/AzureAD/microsoft-authentication-library-for-js) - Authentication
