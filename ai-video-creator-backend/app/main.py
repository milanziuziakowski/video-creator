"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api.v1.router import api_router
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await init_db()
    # Ensure storage directories exist
    settings.storage_uploads.mkdir(parents=True, exist_ok=True)
    settings.storage_output.mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown
    pass


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description="AI Video Creator - 1-Minute Video Studio",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API router
    app.include_router(api_router, prefix="/api/v1")

    # Mount static files for serving uploaded media
    # This serves files from storage/uploads at /uploads URL path
    app.mount("/uploads", StaticFiles(directory=settings.storage_uploads), name="uploads")
    app.mount("/output", StaticFiles(directory=settings.storage_output), name="output")
    app.mount("/temp", StaticFiles(directory=settings.storage_temp), name="temp")

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "app": settings.APP_NAME, "version": app.version}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
