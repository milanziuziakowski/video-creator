"""Pytest configuration and fixtures."""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator, Generator
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.api.v1.router import api_router
from app.db.base import Base
from app.api.deps import get_current_user, get_db
from app.db.models.user import User


# Test database URL (SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


def create_test_app() -> FastAPI:
    """Create test FastAPI app with no-op lifespan (no DB init)."""
    @asynccontextmanager
    async def test_lifespan(app: FastAPI):
        """Test lifespan - no database initialization."""
        yield
    
    test_app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description="AI Video Creator - Test",
        lifespan=test_lifespan,
    )

    # CORS middleware
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API router
    test_app.include_router(api_router, prefix="/api/v1")

    # Health check endpoint
    @test_app.get("/health")
    async def health_check():
        return {"status": "healthy", "app": settings.APP_NAME, "version": test_app.version}

    return test_app


# Create test app instance
app = create_test_app()


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create async engine for testing."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for testing."""
    async_session_maker = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
def test_user() -> User:
    """Create test user fixture."""
    now = datetime.utcnow()
    return User(
        id="test-user-id",
        email="test@example.com",
        username="testuser",
        name="Test User",
        hashed_password="$argon2id$v=19$m=65536,t=3,p=4$test$hashvalue",  # Dummy hash
        is_active=True,
        created_at=now,
        updated_at=now,
    )


# Alias for tests that use mock_user
@pytest.fixture
def mock_user(test_user: User) -> User:
    """Alias for test_user fixture."""
    return test_user


@pytest_asyncio.fixture
async def db_with_user(db_session: AsyncSession, test_user: User) -> AsyncSession:
    """Database session with a test user."""
    db_session.add(test_user)
    await db_session.commit()
    await db_session.refresh(test_user)
    return db_session


@pytest.fixture
def override_get_db(db_session: AsyncSession):
    """Override get_db dependency."""
    async def _override():
        yield db_session
    return _override


@pytest.fixture
def override_get_current_user(test_user: User):
    """Override get_current_user dependency."""
    async def _override():
        return test_user
    return _override


@pytest.fixture
def sync_client(
    override_get_db,
    override_get_current_user,
) -> Generator[TestClient, None, None]:
    """Create sync test client with overridden dependencies (for non-async tests)."""
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession,
    test_user: User,
) -> AsyncIterator[AsyncClient]:
    """Create async test client for e2e tests with user in database."""
    # Ensure user exists in the same session used by the app
    existing = await db_session.get(User, test_user.id)
    if not existing:
        db_session.add(test_user)
        await db_session.commit()
        await db_session.refresh(test_user)

    async def override_get_db():
        yield db_session
    
    async def override_get_current_user():
        return test_user
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


# Alias for tests that expect async_client fixture
@pytest_asyncio.fixture
async def async_client(
    client: AsyncClient,
) -> AsyncClient:
    """Alias for async client fixture."""
    return client


@pytest.fixture
def mock_minimax_client():
    """Mock MiniMax client."""
    with patch("app.integrations.minimax_client.MiniMaxClient") as mock:
        client = MagicMock()
        client.upload_file = AsyncMock(return_value="file-123")
        client.voice_clone = AsyncMock(return_value="voice-123")
        client.text_to_audio = AsyncMock(return_value=b"audio_bytes")
        client.generate_video = AsyncMock(return_value="task-123")
        client.generate_video_fl2v = AsyncMock(return_value="task-123")
        client.query_video_status = AsyncMock(return_value={
            "status": "Success",
            "file_id": "file-123",
        })
        client.poll_video_until_complete = AsyncMock(return_value="/path/to/video.mp4")
        mock.return_value = client
        yield client


@pytest.fixture
def mock_ffmpeg():
    """Mock FFmpeg wrapper."""
    with patch("app.integrations.ffmpeg_wrapper.FFmpegWrapper") as mock:
        wrapper = MagicMock()
        wrapper.extract_last_frame = AsyncMock(return_value="/path/to/frame.jpg")
        wrapper.concat_videos = AsyncMock(return_value="/path/to/concat.mp4")
        wrapper.concat_audios = AsyncMock(return_value="/path/to/concat.mp3")
        wrapper.mux_audio_video = AsyncMock(return_value="/path/to/muxed.mp4")
        wrapper.probe_duration = AsyncMock(return_value=6.0)
        mock.return_value = wrapper
        yield wrapper


@pytest.fixture
def mock_plan_generator():
    """Mock plan generator agent."""
    with patch("app.agents.plan_generator.PlanGeneratorAgent") as mock:
        agent = MagicMock()
        agent.generate_plan = AsyncMock(return_value={
            "segments": [
                {
                    "video_prompt": "A person walking in a park",
                    "narration_text": "On a sunny day, they went for a walk.",
                    "end_frame_prompt": "Person stopping at a bench",
                    "duration_sec": 6,
                },
                {
                    "video_prompt": "Person sitting on a bench",
                    "narration_text": "They sat down to rest.",
                    "end_frame_prompt": "Person relaxing on bench",
                    "duration_sec": 6,
                },
            ]
        })
        mock.return_value = agent
        yield agent
