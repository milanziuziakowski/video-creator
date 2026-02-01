"""API v1 main router."""

from fastapi import APIRouter

from app.api.v1 import auth, projects, segments, generation, media, voices

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(segments.router)
api_router.include_router(generation.router)
api_router.include_router(media.router)
api_router.include_router(voices.router)
