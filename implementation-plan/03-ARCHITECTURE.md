# Architecture Design - AI Video Creator

**Version:** 2.0 (Simplified - No MCP)  
**Last Updated:** January 31, 2026

---

## 1. Architecture Overview

### 1.1 Design Principles

Nowa architektura opiera się na następujących zasadach:

1. **SOLID Principles:**
   - **S**ingle Responsibility - każdy moduł ma jedną odpowiedzialność
   - **O**pen/Closed - rozszerzalność bez modyfikacji istniejącego kodu
   - **L**iskov Substitution - wymienne implementacje interfejsów
   - **I**nterface Segregation - małe, specyficzne interfejsy
   - **D**ependency Inversion - zależność od abstrakcji

2. **Simplicity First:**
   - Bezpośrednie wywołania API zamiast MCP servers
   - Monolityczny backend zamiast mikrousług
   - Prosty state management

3. **Human-in-the-Loop Native:**
   - Architektura zaprojektowana wokół HITL workflow
   - Explicit approval gates w każdym kroku

4. **Best Practices Integration:**
   - OpenAI Agents SDK patterns
   - MiniMax API best practices
   - React/TypeScript conventions

---

## 2. High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React + TypeScript)                      │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌──────────────────┐  │
│  │   Auth      │  │   Project    │  │   HITL      │  │   Video          │  │
│  │   Pages     │  │   Dashboard  │  │   Workflow  │  │   Player         │  │
│  └─────────────┘  └──────────────┘  └─────────────┘  └──────────────────┘  │
│                              │                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    API Layer (React Query + Middleware)              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ HTTPS/REST + WebSocket
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BACKEND (FastAPI + Python)                         │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                         API Router Layer                            │    │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │    │
│  │   │ /auth    │  │ /projects│  │ /segments│  │ /generation      │  │    │
│  │   └──────────┘  └──────────┘  └──────────┘  └──────────────────┘  │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                      │                                       │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                        Service Layer                                │    │
│  │   ┌───────────────┐  ┌───────────────┐  ┌───────────────────────┐ │    │
│  │   │ Project       │  │ Orchestrator  │  │ Media                 │ │    │
│  │   │ Service       │  │ Service       │  │ Service               │ │    │
│  │   └───────────────┘  └───────────────┘  └───────────────────────┘ │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                      │                                       │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                      Integration Layer                              │    │
│  │   ┌───────────────┐  ┌───────────────┐  ┌───────────────────────┐ │    │
│  │   │ OpenAI        │  │ MiniMax       │  │ FFmpeg                │ │    │
│  │   │ Agents Client │  │ API Client    │  │ Wrapper               │ │    │
│  │   └───────────────┘  └───────────────┘  └───────────────────────┘ │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                      │                                       │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                       Data Layer                                    │    │
│  │   ┌───────────────┐  ┌───────────────┐  ┌───────────────────────┐ │    │
│  │   │ Repositories  │  │ Models        │  │ Storage               │ │    │
│  │   │ (SQLAlchemy)  │  │ (Pydantic)    │  │ (File System)         │ │    │
│  │   └───────────────┘  └───────────────┘  └───────────────────────┘ │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              ▼                       ▼                       ▼
    ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
    │   PostgreSQL/    │   │   OpenAI API     │   │   MiniMax API    │
    │   SQLite         │   │   (Agents SDK)   │   │   (Video/Audio)  │
    └──────────────────┘   └──────────────────┘   └──────────────────┘
```

---

## 3. Frontend Architecture (React)

### 3.1 Diagram architektury Frontend

```
┌─────────────────────────────────────────────────────────────────────┐
│                        React Application                             │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    App Shell (Layout)                        │   │
│  │   ┌─────────────┐  ┌────────────────┐  ┌──────────────────┐ │   │
│  │   │ Navigation  │  │ Auth Provider  │  │ Error Boundary   │ │   │
│  │   │ Bar         │  │ (MSAL)         │  │                  │ │   │
│  │   └─────────────┘  └────────────────┘  └──────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                         Pages                                 │   │
│  │   ┌──────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐ │   │
│  │   │ Login    │  │ Dashboard │  │ Project   │  │ Workflow  │ │   │
│  │   │ Page     │  │ Page      │  │ Detail    │  │ Page      │ │   │
│  │   └──────────┘  └───────────┘  └───────────┘  └───────────┘ │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                      Components                               │   │
│  │   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │   │
│  │   │ MediaUploader   │  │ PromptEditor    │  │ VideoPlayer │ │   │
│  │   │ - FirstFrame    │  │ - PromptCard    │  │ - Controls  │ │   │
│  │   │ - LastFrame     │  │ - EditModal     │  │ - Preview   │ │   │
│  │   │ - AudioUpload   │  │ - PromptInput   │  │ - Timeline  │ │   │
│  │   └─────────────────┘  └─────────────────┘  └─────────────┘ │   │
│  │                                                               │   │
│  │   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │   │
│  │   │ SegmentList     │  │ GenerationStatus│  │ ApprovalGate│ │   │
│  │   │ - SegmentCard   │  │ - Progress      │  │ - Buttons   │ │   │
│  │   │ - Timeline      │  │ - Spinner       │  │ - Actions   │ │   │
│  │   └─────────────────┘  └─────────────────┘  └─────────────┘ │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     State Management                          │   │
│  │   ┌─────────────┐  ┌─────────────┐  ┌────────────────────┐  │   │
│  │   │ React Query │  │ Context     │  │ Local State        │  │   │
│  │   │ (Server)    │  │ (Global)    │  │ (Component)        │  │   │
│  │   └─────────────┘  └─────────────┘  └────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     API Middleware                            │   │
│  │   ┌─────────────┐  ┌─────────────┐  ┌────────────────────┐  │   │
│  │   │ apiClient   │  │ authInterc. │  │ errorHandler       │  │   │
│  │   │ (Axios)     │  │             │  │                    │  │   │
│  │   └─────────────┘  └─────────────┘  └────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Folder Structure

```
frontend/
├── public/
│   ├── index.html
│   ├── favicon.ico
│   └── assets/
│       └── images/
├── src/
│   ├── index.tsx                 # Entry point
│   ├── App.tsx                   # Main app component
│   ├── authConfig.ts             # MSAL configuration
│   ├── vite-env.d.ts
│   │
│   ├── assets/                   # Static assets
│   │   └── images/
│   │
│   ├── components/               # Reusable components
│   │   ├── common/
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Spinner.tsx
│   │   │   └── ErrorBoundary.tsx
│   │   ├── auth/
│   │   │   ├── LoginButton.tsx
│   │   │   └── LogoutButton.tsx
│   │   ├── media/
│   │   │   ├── FirstFrameUploader.tsx
│   │   │   ├── LastFrameUploader.tsx
│   │   │   ├── DualFrameUploader.tsx    # Combined first+last frame upload
│   │   │   ├── AudioUploader.tsx
│   │   │   └── VideoPlayer.tsx
│   │   ├── project/
│   │   │   ├── ProjectCard.tsx
│   │   │   ├── ProjectList.tsx
│   │   │   └── CreateProjectForm.tsx
│   │   ├── workflow/
│   │   │   ├── PromptEditor.tsx
│   │   │   ├── SegmentCard.tsx
│   │   │   ├── SegmentTimeline.tsx
│   │   │   ├── ApprovalGate.tsx
│   │   │   └── GenerationProgress.tsx
│   │   └── layout/
│   │       ├── Header.tsx
│   │       ├── Sidebar.tsx
│   │       └── Footer.tsx
│   │
│   ├── layouts/                  # Page layouts
│   │   ├── AuthLayout.tsx
│   │   └── MainLayout.tsx
│   │
│   ├── pages/                    # Route pages
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── ProjectDetailPage.tsx
│   │   ├── WorkflowPage.tsx
│   │   └── api/                  # API route handlers (if using Next.js-style)
│   │       └── projects.ts
│   │
│   ├── hooks/                    # Custom hooks
│   │   ├── useAuth.ts
│   │   ├── useProjects.ts
│   │   ├── useSegments.ts
│   │   ├── useGeneration.ts
│   │   └── usePolling.ts
│   │
│   ├── services/                 # API services
│   │   ├── api.ts               # Base API client
│   │   ├── authService.ts
│   │   ├── projectService.ts
│   │   ├── segmentService.ts
│   │   └── generationService.ts
│   │
│   ├── types/                    # TypeScript types
│   │   ├── index.ts
│   │   ├── project.ts
│   │   ├── segment.ts
│   │   └── generation.ts
│   │
│   ├── utils/                    # Utility functions
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   └── storage.ts
│   │
│   └── context/                  # React contexts
│       ├── AuthContext.tsx
│       └── ProjectContext.tsx
│
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── vite.config.ts
└── .env.example
```

---

## 4. Backend Architecture (Python/FastAPI)

### 4.1 Diagram architektury Backend

```
┌─────────────────────────────────────────────────────────────────────┐
│                       FastAPI Application                            │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                      API Layer                               │   │
│  │                                                               │   │
│  │   /api/v1/                                                   │   │
│  │   ├── /auth                                                  │   │
│  │   │   ├── POST /login                                        │   │
│  │   │   ├── POST /logout                                       │   │
│  │   │   └── GET  /me                                           │   │
│  │   │                                                          │   │
│  │   ├── /projects                                              │   │
│  │   │   ├── GET    /              (list projects)              │   │
│  │   │   ├── POST   /              (create project)             │   │
│  │   │   ├── GET    /{id}          (get project)                │   │
│  │   │   ├── PUT    /{id}          (update project)             │   │
│  │   │   ├── DELETE /{id}          (delete project)             │   │
│  │   │   └── POST   /{id}/finalize (finalize video)             │   │
│  │   │                                                          │   │
│  │   ├── /segments                                              │   │
│  │   │   ├── GET    /project/{id}  (list segments)              │   │
│  │   │   ├── GET    /{id}          (get segment)                │   │
│  │   │   ├── PUT    /{id}          (update segment)             │   │
│  │   │   ├── POST   /{id}/approve  (approve segment)            │   │
│  │   │   └── POST   /{id}/regenerate (regenerate)               │   │
│  │   │                                                          │   │
│  │   ├── /generation                                            │   │
│  │   │   ├── POST   /plan          (generate AI plan)           │   │
│  │   │   ├── POST   /voice-clone   (clone voice)                │   │
│  │   │   ├── POST   /segment/{id}  (generate segment)           │   │
│  │   │   └── GET    /status/{task} (poll status)                │   │
│  │   │                                                          │   │
│  │   └── /media                                                 │   │
│  │       ├── POST   /upload/first-frame   (upload first frame)  │   │
│  │       ├── POST   /upload/last-frame    (upload last frame)   │   │
│  │       ├── POST   /upload/frames        (upload both frames)  │   │
│  │       ├── POST   /upload/audio         (upload voice sample) │   │
│  │       └── GET    /download/{id}        (download video)      │   │
│  │                                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Service Layer                             │   │
│  │                                                               │   │
│  │   ┌─────────────────────────────────────────────────────┐   │   │
│  │   │               ProjectService                         │   │   │
│  │   │  - create_project()                                  │   │   │
│  │   │  - get_project()                                     │   │   │
│  │   │  - update_project()                                  │   │   │
│  │   │  - delete_project()                                  │   │   │
│  │   │  - finalize_project()                                │   │   │
│  │   └─────────────────────────────────────────────────────┘   │   │
│  │                                                               │   │
│  │   ┌─────────────────────────────────────────────────────┐   │   │
│  │   │               OrchestratorService                    │   │   │
│  │   │  - generate_video_plan()     [OpenAI Agents]         │   │   │
│  │   │  - process_segment()         [Coordinates all]       │   │   │
│  │   │  - clone_voice()                                     │   │   │
│  │   │  - generate_audio()                                  │   │   │
│  │   │  - generate_video()                                  │   │   │
│  │   └─────────────────────────────────────────────────────┘   │   │
│  │                                                               │   │
│  │   ┌─────────────────────────────────────────────────────┐   │   │
│  │   │               MediaService                           │   │   │
│  │   │  - extract_last_frame()      [FFmpeg]                │   │   │
│  │   │  - concat_videos()           [FFmpeg]                │   │   │
│  │   │  - concat_audios()           [FFmpeg]                │   │   │
│  │   │  - mux_audio_video()         [FFmpeg]                │   │   │
│  │   │  - probe_duration()          [FFmpeg]                │   │   │
│  │   └─────────────────────────────────────────────────────┘   │   │
│  │                                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  Integration Layer                           │   │
│  │                                                               │   │
│  │   ┌──────────────────────┐  ┌─────────────────────────────┐ │   │
│  │   │   OpenAIAgentClient  │  │      MinimaxClient          │ │   │
│  │   │                      │  │                             │ │   │
│  │   │  Uses Agents SDK:    │  │  Direct API calls:          │ │   │
│  │   │  - Agent             │  │  - upload_file()            │ │   │
│  │   │  - Runner            │  │  - voice_clone()            │ │   │
│  │   │  - handoffs          │  │  - text_to_audio()          │ │   │
│  │   │  - tools             │  │  - generate_video()         │ │   │
│  │   │                      │  │  - query_status()           │ │   │
│  │   └──────────────────────┘  │  - retrieve_file()          │ │   │
│  │                              └─────────────────────────────┘ │   │
│  │   ┌──────────────────────────────────────────────────────┐  │   │
│  │   │                   FFmpegWrapper                       │  │   │
│  │   │  - extract_frame()                                    │  │   │
│  │   │  - concat()                                           │  │   │
│  │   │  - mux()                                              │  │   │
│  │   │  - probe()                                            │  │   │
│  │   └──────────────────────────────────────────────────────┘  │   │
│  │                                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     Data Layer                               │   │
│  │                                                               │   │
│  │   ┌─────────────────────────────────────────────────────┐   │   │
│  │   │                   Repositories                       │   │   │
│  │   │  - ProjectRepository                                 │   │   │
│  │   │  - SegmentRepository                                 │   │   │
│  │   │  - UserRepository                                    │   │   │
│  │   └─────────────────────────────────────────────────────┘   │   │
│  │                                                               │   │
│  │   ┌─────────────────────────────────────────────────────┐   │   │
│  │   │                   Models (Pydantic)                  │   │   │
│  │   │  - Project, ProjectCreate, ProjectUpdate             │   │   │
│  │   │  - Segment, SegmentStatus                            │   │   │
│  │   │  - VideoPlan, VideoStoryPlan                         │   │   │
│  │   │  - GenerationTask, GenerationStatus                  │   │   │
│  │   └─────────────────────────────────────────────────────┘   │   │
│  │                                                               │   │
│  │   ┌─────────────────────────────────────────────────────┐   │   │
│  │   │                   Database (ORM)                     │   │   │
│  │   │  - SQLAlchemy models                                 │   │   │
│  │   │  - Alembic migrations                                │   │   │
│  │   └─────────────────────────────────────────────────────┘   │   │
│  │                                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Folder Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Settings & configuration
│   ├── dependencies.py            # Dependency injection
│   │
│   ├── api/                       # API endpoints
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py          # Main router
│   │   │   ├── auth.py
│   │   │   ├── projects.py
│   │   │   ├── segments.py
│   │   │   ├── generation.py
│   │   │   └── media.py
│   │   └── deps.py                # Route dependencies
│   │
│   ├── services/                  # Business logic
│   │   ├── __init__.py
│   │   ├── project_service.py
│   │   ├── orchestrator_service.py
│   │   ├── media_service.py
│   │   └── auth_service.py
│   │
│   ├── integrations/              # External API clients
│   │   ├── __init__.py
│   │   ├── openai_client.py       # OpenAI Agents SDK
│   │   ├── minimax_client.py      # MiniMax API (direct)
│   │   └── ffmpeg_wrapper.py      # FFmpeg operations
│   │
│   ├── models/                    # Pydantic models
│   │   ├── __init__.py
│   │   ├── project.py
│   │   ├── segment.py
│   │   ├── video_plan.py
│   │   ├── generation.py
│   │   └── user.py
│   │
│   ├── db/                        # Database
│   │   ├── __init__.py
│   │   ├── base.py                # SQLAlchemy base
│   │   ├── session.py             # Session factory
│   │   └── models/                # ORM models
│   │       ├── __init__.py
│   │       ├── project.py
│   │       ├── segment.py
│   │       └── user.py
│   │
│   ├── repositories/              # Data access
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── project_repository.py
│   │   ├── segment_repository.py
│   │   └── user_repository.py
│   │
│   ├── agents/                    # OpenAI Agents definitions
│   │   ├── __init__.py
│   │   ├── supervisor_agent.py    # Video planning agent
│   │   ├── frame_designer_agent.py
│   │   └── tools/                 # Agent tools
│   │       ├── __init__.py
│   │       └── planning_tools.py
│   │
│   └── utils/                     # Utilities
│       ├── __init__.py
│       ├── storage.py
│       └── validators.py
│
├── migrations/                    # Alembic migrations
│   ├── versions/
│   └── env.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api/
│   ├── test_services/
│   └── e2e/
│
├── storage/                       # Local file storage
│   ├── uploads/
│   ├── temp/
│   └── output/
│
├── pyproject.toml
├── requirements.txt
├── alembic.ini
├── Dockerfile
└── .env.example
```

---

## 5. OpenAI Agents SDK Integration

### 5.1 Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    OpenAI Agents Orchestration                       │
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                    Supervisor Agent                          │  │
│   │                                                              │  │
│   │   Instructions:                                              │  │
│   │   - Create cohesive video plans                              │  │
│   │   - Generate cinematic prompts                               │  │
│   │   - Ensure visual continuity                                 │  │
│   │   - Write narration scripts                                  │  │
│   │                                                              │  │
│   │   Tools:                                                     │  │
│   │   - create_video_plan()                                      │  │
│   │   - generate_segment_prompt()                                │  │
│   │                                                              │  │
│   │   Handoffs:                                                  │  │
│   │   - → Frame Designer Agent (for end-frame generation)        │  │
│   │                                                              │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│                              │ handoff                               │
│                              ▼                                       │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                  Frame Designer Agent                        │  │
│   │                                                              │  │
│   │   Instructions:                                              │  │
│   │   - Design end-frame descriptions                            │  │
│   │   - Ensure smooth transitions                                │  │
│   │   - Maintain visual style                                    │  │
│   │                                                              │  │
│   │   Tools:                                                     │  │
│   │   - generate_end_frame_prompt()                              │  │
│   │                                                              │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                       Runner                                 │  │
│   │                                                              │  │
│   │   - Runs agent loop                                          │  │
│   │   - Handles tool invocations                                 │  │
│   │   - Manages handoffs                                         │  │
│   │   - Returns structured results                               │  │
│   │                                                              │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Agent Code Structure

```python
# backend/app/agents/supervisor_agent.py
from agents import Agent, handoff, Runner
from app.agents.frame_designer_agent import frame_designer_agent
from app.agents.tools.planning_tools import (
    create_video_plan,
    generate_segment_prompt,
)

supervisor_agent = Agent(
    name="Video Supervisor",
    instructions="""You are an expert video story planner...
    
    Your responsibilities:
    1. Break down story concepts into segments
    2. Generate cinematic video prompts
    3. Write compelling narration
    4. Ensure visual continuity
    
    When you need detailed end-frame descriptions,
    hand off to the Frame Designer agent.
    """,
    tools=[create_video_plan, generate_segment_prompt],
    handoffs=[frame_designer_agent],
)

async def generate_plan(story_prompt: str, segment_count: int):
    result = await Runner.run(
        supervisor_agent,
        f"Create a video plan for: {story_prompt} with {segment_count} segments"
    )
    return result.final_output
```

---

## 6. MiniMax API Integration (Direct - No MCP)

### 6.1 API Client Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     MinimaxClient                                    │
│                                                                      │
│   Base Configuration:                                               │
│   - API_BASE = "https://api.minimax.io/v1"                         │
│   - Timeout = 120s                                                  │
│   - Retry with exponential backoff                                  │
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                   File Operations                            │  │
│   │   - upload_file(bytes, filename, purpose) → file_id          │  │
│   │   - retrieve_file(file_id) → download_url                    │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                   Voice Operations                           │  │
│   │   - voice_clone(file_id, voice_name) → voice_id              │  │
│   │   - text_to_audio(text, voice_id) → audio_url                │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                   Video Operations                           │  │
│   │   - generate_video(prompt, first_frame, last_frame,          │  │
│   │                    duration, resolution) → task_id           │  │
│   │   - query_video_status(task_id) → status, file_id            │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                   Polling Utilities                          │  │
│   │   - poll_until_complete(task_id, interval=10s) → result      │  │
│   │   - with timeout and max retries                             │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Video Generation Flow (First + Last Frame with Prompt) - FL2V API

The MiniMax API supports **First & Last Frame Video Generation (FL2V)** using the
`POST /v1/video_generation` endpoint with model `MiniMax-Hailuo-02`.

#### 6.2.1 FL2V API Specification

**Endpoint:** `POST https://api.minimax.io/v1/video_generation`

**Authentication:** `Authorization: Bearer <API_KEY>`

**Request Body:**
```json
{
  "model": "MiniMax-Hailuo-02",           // Required: Only model supporting FL2V
  "first_frame_image": "url_or_base64",   // Optional: URL or data:image/jpeg;base64,...
  "last_frame_image": "url_or_base64",    // Required for FL2V: URL or Base64
  "prompt": "Video description...",        // Optional: Up to 2000 characters
  "duration": 6,                          // Optional: 6 or 10 seconds (default: 6)
  "resolution": "768P",                   // Optional: 768P or 1080P (default: 768P)
  "prompt_optimizer": true,               // Optional: Auto-optimize prompt (default: true)
  "callback_url": "https://..."           // Optional: Webhook for status updates
}
```

**Image Requirements:**
- Formats: JPG, JPEG, PNG, WebP
- Size: < 20MB
- Dimensions: Short side > 300px, Aspect ratio 2:5 to 5:2
- Resolution: Video resolution follows first_frame_image
- Note: last_frame_image will be cropped to match first_frame_image dimensions

**Camera Commands (embed in prompt):**
```
Supported commands (use [command] syntax):
- Truck: [Truck left], [Truck right]
- Pan: [Pan left], [Pan right]
- Push: [Push in], [Pull out]
- Pedestal: [Pedestal up], [Pedestal down]
- Tilt: [Tilt up], [Tilt down]
- Zoom: [Zoom in], [Zoom out]
- Shake: [Shake]
- Follow: [Tracking shot]
- Static: [Static shot]

Combined: [Pan left,Pedestal up] (max 3 simultaneous)
Sequential: "...[Push in], then...[Pull out]"
```

**Response:**
```json
{
  "task_id": "106916112212032",
  "base_resp": {
    "status_code": 0,
    "status_msg": "success"
  }
}
```

#### 6.2.2 FL2V Generation Flow Diagram

```
User uploads first_frame_image AND last_frame_image (from PC or provides URLs)
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Validate Images                                          │
│    - Format: JPG, JPEG, PNG, WebP                          │
│    - Size: < 20MB each                                      │
│    - Dimensions: Short side > 300px                         │
│    - Aspect ratio: 2:5 to 5:2                               │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Prepare Images (choose one method)                       │
│    Option A: Upload to get public URL                       │
│    Option B: Convert to Base64 data URL                     │
│    Format: data:image/jpeg;base64,<base64_data>             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Generate Video (FL2V)       │ POST /v1/video_generation  │
│    Parameters:                 │ Body: {                    │
│    - model: MiniMax-Hailuo-02  │   "model": "MiniMax-Hailuo-02",│
│    - first_frame_image (opt)   │   "first_frame_image": "...",  │
│    - last_frame_image (req)    │   "last_frame_image": "...",   │
│    - prompt (max 2000 chars)   │   "prompt": "A girl grows up [Zoom in]",│
│    - duration (6 or 10 sec)    │   "duration": 6,               │
│    - resolution (768P/1080P)   │   "resolution": "1080P",       │
│    - prompt_optimizer          │   "prompt_optimizer": false    │
│    → task_id                   │ }                              │
│                                │ Note: 512P NOT supported for FL2V│
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Poll Status             │ GET /query/video_generation    │
│    (every 10s recommended) │   ?task_id=...                 │
│    → status                │ Response: {                    │
│    → file_id               │   "status": "Success"|         │
│                            │            "processing"|"Fail",│
│                            │   "file_id": "..."             │
│                            │ }                              │
└─────────────────────────────────────────────────────────────┘
         │                   
         ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Retrieve File           │ GET /files/retrieve?file_id=  │
│    → download_url          │ Response: {                    │
│                            │   "file": {"download_url":...} │
│                            │ }                              │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Download Video          │ GET download_url               │
│    → video bytes           │ (ready for concatenation)      │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 Segment Generation with Dual Frames

For video continuity between segments, the system supports two modes:

**Mode 1: User-Provided Frames (Manual Control)**
- User uploads both first_frame and last_frame images from PC
- User provides custom prompt text
- Best for: specific scene requirements, artistic control

**Mode 2: Automatic Frame Extraction (Seamless Transitions)**
- First frame: Extracted as last frame from previous segment (FFmpeg)
- Last frame: AI-generated based on prompt + frame designer agent
- Best for: continuous story flow, automated workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│              Segment Generation Modes                                │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  MODE 1: Manual Dual-Frame Upload                              │ │
│  │  ─────────────────────────────────────────────────────────────│ │
│  │  User provides:                                                │ │
│  │  - First frame image (from PC)                                 │ │
│  │  - Last frame image (from PC)                                  │ │
│  │  - Custom prompt text describing motion/transition             │ │
│  │                                                                │ │
│  │  Use case: Creative control, specific scene requirements       │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  MODE 2: Automatic with AI-Generated End Frame                 │ │
│  │  ─────────────────────────────────────────────────────────────│ │
│  │  System provides:                                              │ │
│  │  - First frame: Last frame of previous segment (FFmpeg)        │ │
│  │  - Last frame: Generated description (Frame Designer Agent)    │ │
│  │  - Prompt: AI-generated (Supervisor Agent)                     │ │
│  │                                                                │ │
│  │  Use case: Automated story flow, seamless transitions          │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 7. Human-in-the-Loop (HITL) Workflow

### 7.1 HITL State Machine

```
                    ┌────────────────────────┐
                    │     PROJECT_CREATED    │
                    └────────────────────────┘
                              │
                              ▼
                    ┌────────────────────────┐
                    │    MEDIA_UPLOADED      │
                    │  (image + audio)       │
                    └────────────────────────┘
                              │
                              ▼
                    ┌────────────────────────┐
                    │   VOICE_CLONING        │
                    └────────────────────────┘
                              │
                              ▼
                    ┌────────────────────────┐
                    │   PLAN_GENERATING      │
                    │   (OpenAI Agents)      │
                    └────────────────────────┘
                              │
                              ▼
                    ┌────────────────────────┐
                    │   PLAN_READY           │◄───────────────┐
                    │   (awaiting approval)  │                │
                    └────────────────────────┘                │
                              │                               │
              ┌───────────────┴───────────────┐               │
              ▼                               ▼               │
    ┌──────────────────┐           ┌──────────────────┐       │
    │  PROMPT_EDITING  │───────────│  PROMPT_APPROVED │       │
    │  (user editing)  │           │                  │       │
    └──────────────────┘           └──────────────────┘       │
                                            │                 │
                                            ▼                 │
                                  ┌──────────────────┐        │
                                  │   GENERATING     │        │
                                  │ (video + audio)  │        │
                                  └──────────────────┘        │
                                            │                 │
                                            ▼                 │
                                  ┌──────────────────┐        │
                                  │ SEGMENT_READY    │        │
                                  │(awaiting review) │        │
                                  └──────────────────┘        │
                                            │                 │
                      ┌─────────────────────┴─────────────────┐
                      ▼                                       ▼
           ┌──────────────────┐                    ┌──────────────────┐
           │ SEGMENT_APPROVED │                    │   REGENERATE     │
           └──────────────────┘                    └──────────────────┘
                      │                                       │
                      ▼                                       │
           ┌──────────────────┐                               │
           │  Next Segment?   │───────────────────────────────┘
           │   Yes → PLAN_READY (next segment)                │
           │   No  → FINALIZING                               │
           └──────────────────┘                               │
                      │                                       │
                      ▼                                       │
           ┌──────────────────┐                               │
           │   FINALIZING     │                               │
           │ (concat + mux)   │                               │
           └──────────────────┘                               │
                      │                                       │
                      ▼                                       │
           ┌──────────────────┐                               │
           │    COMPLETED     │                               │
           │ (video ready)    │                               │
           └──────────────────┘                               │
```

---

## 8. Data Model

### 8.1 Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Database Schema                             │
│                                                                      │
│   ┌───────────────┐                                                 │
│   │    users      │                                                 │
│   ├───────────────┤                                                 │
│   │ id (PK)       │                                                 │
│   │ entra_id      │                                                 │
│   │ email         │                                                 │
│   │ name          │                                                 │
│   │ created_at    │                                                 │
│   └───────────────┘                                                 │
│          │                                                          │
│          │ 1:N                                                      │
│          ▼                                                          │
│   ┌───────────────┐           ┌───────────────┐                    │
│   │   projects    │           │   segments    │                    │
│   ├───────────────┤           ├───────────────┤                    │
│   │ id (PK)       │──────────▶│ id (PK)       │                    │
│   │ user_id (FK)  │    1:N    │ project_id(FK)│                    │
│   │ name          │           │ index         │                    │
│   │ story_prompt  │           │ video_prompt  │ ← User-editable    │
│   │ target_dur    │           │ narration_text│                    │
│   │ segment_len   │           │ end_frame_pr  │                    │
│   │ segment_count │           │ first_frame   │ ← Can be uploaded  │
│   │ voice_id      │           │ last_frame    │ ← Can be uploaded  │
│   │ first_frame   │           │ first_frame_  │                    │
│   │ audio_sample  │           │   source      │ (uploaded/extract) │
│   │ status        │           │ last_frame_   │                    │
│   │ final_video   │           │   source      │ (uploaded/ai_gen)  │
│   │ created_at    │           │ video_url     │                    │
│   │ updated_at    │           │ audio_url     │                    │
│   └───────────────┘           │ status        │                    │
│                               │ approved      │                    │
│                               │ created_at    │                    │
│                               │ updated_at    │                    │
│                               └───────────────┘                    │
│                                                                      │
│   Status Enums:                                                     │
│   - Project: created, media_uploaded, voice_cloning,                │
│              plan_generating, plan_ready, generating,               │
│              finalizing, completed, failed                          │
│   - Segment: pending, prompt_ready, approved, generating,           │
│              generated, approved, failed                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 9. Security Architecture

### 9.1 Authentication Flow

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   React SPA     │      │   Azure Entra   │      │   FastAPI       │
│   (Frontend)    │      │   ID            │      │   (Backend)     │
└─────────────────┘      └─────────────────┘      └─────────────────┘
        │                         │                        │
        │  1. Login Click         │                        │
        │─────────────────────────▶                        │
        │                         │                        │
        │  2. Redirect to         │                        │
        │     Entra Login         │                        │
        │◀─────────────────────────                        │
        │                         │                        │
        │  3. User authenticates  │                        │
        │─────────────────────────▶                        │
        │                         │                        │
        │  4. Redirect with       │                        │
        │     Authorization Code  │                        │
        │◀─────────────────────────                        │
        │                         │                        │
        │  5. Exchange code       │                        │
        │     for tokens (MSAL)   │                        │
        │─────────────────────────▶                        │
        │                         │                        │
        │  6. ID Token +          │                        │
        │     Access Token        │                        │
        │◀─────────────────────────                        │
        │                                                  │
        │  7. API Request with Bearer Token                │
        │─────────────────────────────────────────────────▶│
        │                                                  │
        │                                   8. Validate    │
        │                                      Token       │
        │                                                  │
        │  9. Protected Resource                           │
        │◀─────────────────────────────────────────────────│
        │                                                  │
```

---

## 10. Deployment Architecture (Azure)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Azure Cloud                                   │
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                  Azure Entra ID                              │  │
│   │   - App Registration                                         │  │
│   │   - User authentication                                      │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
│   ┌──────────────────────┐    ┌──────────────────────────────────┐ │
│   │   Azure Static       │    │   Azure App Service              │ │
│   │   Web Apps           │    │   (Linux Container)              │ │
│   │   ─────────────────  │    │   ────────────────────────────   │ │
│   │   React Frontend     │───▶│   FastAPI Backend                │ │
│   │   (Build & Deploy)   │    │   Python 3.11+                   │ │
│   └──────────────────────┘    │   FFmpeg installed               │ │
│                               └──────────────────────────────────┘ │
│                                              │                      │
│                                              ▼                      │
│                               ┌──────────────────────────────────┐ │
│                               │   Azure Database for PostgreSQL  │ │
│                               │   (Flexible Server)              │ │
│                               └──────────────────────────────────┘ │
│                                                                      │
│   ┌──────────────────────────────────────────────────────────────┐ │
│   │                  Azure Blob Storage                           │ │
│   │   - Uploaded images                                           │ │
│   │   - Uploaded audio samples                                    │ │
│   │   - Generated videos                                          │ │
│   │   - Generated audio                                           │ │
│   └──────────────────────────────────────────────────────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      External Services                               │
│                                                                      │
│   ┌──────────────────────┐    ┌──────────────────────────────────┐ │
│   │   OpenAI API         │    │   MiniMax API                    │ │
│   │   (Agents SDK)       │    │   (Video/Audio Generation)       │ │
│   └──────────────────────┘    └──────────────────────────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 11. Key Changes from Previous Architecture

| Aspect | Poprzednia architektura | Nowa architektura |
|--------|------------------------|-------------------|
| **MCP Servers** | 3 MCP servers (MiniMax, FL2V, MediaOps) | Bezpośrednie wywołania API |
| **Complexity** | Wysoka (MCP transport, protocols) | Niska (REST API client) |
| **OpenAI Integration** | Basic chat completions | OpenAI Agents SDK (handoffs, tools) |
| **Frontend** | Brak (CLI/scripts) | React + TypeScript SPA |
| **Authentication** | Brak | Azure Entra ID |
| **Persistence** | Minimal (file-based) | PostgreSQL + SQLAlchemy |
| **Deployment** | Manual | Azure + CI/CD |
| **HITL** | Basic approval loop | Full state machine |
