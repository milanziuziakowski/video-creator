# AI Video Creator Backend

A FastAPI backend for creating AI-powered videos using MiniMax API, OpenAI Agents SDK, and FFmpeg.

## Features

- 🎬 AI-powered video generation using MiniMax Hailuo-02 (FL2V)
- 🗣️ Voice cloning and text-to-speech with MiniMax API
- 📝 Intelligent video planning with OpenAI Agents SDK
- 🔄 Human-in-the-loop workflow for prompt review
- 🔐 JWT-based authentication with username/password
- 📦 PostgreSQL database with async support

## Prerequisites

- Python 3.11+
- FFmpeg (for video/audio processing)
- PostgreSQL (for production) or SQLite (for development)
- uv (recommended) or pip

## Quick Start

### 1. Clone and Setup Environment

```bash
cd ai-video-creator-backend

# Install uv if not already installed
pip install uv

# Create virtual environment and install dependencies
uv venv
uv pip install -e ".[dev]"
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

### 3. Run Database Migrations

```bash
alembic upgrade head
```

### 4. Start Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
ai-video-creator-backend/
├── app/
│   ├── api/              # API routes and dependencies
│   │   ├── deps.py       # Shared dependencies
│   │   └── v1/           # v1 API routes
│   ├── agents/           # OpenAI Agents SDK integration
│   ├── auth/             # JWT authentication
│   ├── db/               # Database models and session
│   ├── integrations/     # External API clients
│   ├── models/           # Pydantic schemas
│   ├── services/         # Business logic
│   ├── config.py         # Application configuration
│   └── main.py           # FastAPI application
├── alembic/              # Database migrations
├── tests/                # Test suite
├── Dockerfile            # Production Docker image
├── pyproject.toml        # Project dependencies
└── README.md
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_projects.py -v
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy app
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## Docker

### Build Image

```bash
docker build -t ai-video-creator-backend .
```

### Run Container

```bash
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e MINIMAX_API_KEY=... \
  -e OPENAI_API_KEY=... \
  -e JWT_SECRET_KEY=your-secret-key \
  ai-video-creator-backend
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/token` - Login and get access token
- `POST /api/v1/auth/register` - Register new user
- `GET /api/v1/auth/me` - Get current user info

### Projects
- `GET /api/v1/projects/` - List user projects
- `POST /api/v1/projects/` - Create new project
- `GET /api/v1/projects/{id}` - Get project details
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project
- `POST /api/v1/projects/{id}/finalize` - Finalize and concatenate video

### Segments
- `GET /api/v1/segments/project/{project_id}` - List project segments
- `GET /api/v1/segments/{id}` - Get segment details
- `PUT /api/v1/segments/{id}` - Update segment prompts
- `POST /api/v1/segments/{id}/approve` - Approve segment prompt
- `POST /api/v1/segments/{id}/approve-video` - Approve generated video
- `POST /api/v1/segments/{id}/regenerate` - Request regeneration

### Generation
- `POST /api/v1/generation/plan` - Generate AI video plan
- `POST /api/v1/generation/voice-clone` - Clone voice from audio
- `POST /api/v1/generation/segment/{id}` - Start segment generation
- `GET /api/v1/generation/status/{task_id}` - Poll generation status

### Media
- `POST /api/v1/media/upload/first-frame` - Upload first frame image
- `POST /api/v1/media/upload/audio` - Upload voice sample
- `POST /api/v1/media/upload/segment-frame/{id}` - Upload segment frame
- `GET /api/v1/media/download/{project_id}/final` - Download final video

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| DATABASE_URL | PostgreSQL connection string | Yes |
| MINIMAX_API_KEY | MiniMax API key | Yes |
| MINIMAX_GROUP_ID | MiniMax group ID | Yes |
| OPENAI_API_KEY | OpenAI API key | Yes |
| JWT_SECRET_KEY | Secret key for JWT tokens | Yes |
| JWT_ALGORITHM | JWT algorithm (default: HS256) | No |
| ACCESS_TOKEN_EXPIRE_MINUTES | Token expiration time | No |
| CORS_ORIGINS | Allowed CORS origins | No |
| UPLOAD_DIR | Upload directory path | No |
| OUTPUT_DIR | Output directory path | No |

## License

Proprietary - All rights reserved
