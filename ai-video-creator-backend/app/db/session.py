"""Database session management."""

from collections.abc import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.db.base import Base

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Initialize database - create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed dev user in development mode
    if settings.is_development:
        await seed_dev_user()


async def seed_dev_user() -> None:
    """Seed development user for testing."""
    from app.auth.jwt_auth import get_password_hash
    from app.db.models.user import User

    async with async_session_factory() as session:
        # Check if dev user exists
        result = await session.execute(select(User).where(User.id == "dev-user-id"))
        existing_user = result.scalar_one_or_none()

        if existing_user is None:
            # Create dev user
            dev_user = User(
                id="dev-user-id",
                username="dev@example.com",
                email="dev@example.com",
                name="Dev User",
                hashed_password=get_password_hash("devpassword"),
                is_active=True,
            )
            session.add(dev_user)
            await session.commit()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session - FastAPI dependency."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
