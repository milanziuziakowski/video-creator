"""Tests for auth endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_current_user(async_client: AsyncClient, test_user):
    """Test getting current user info."""
    response = await async_client.get("/api/v1/auth/me")
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["name"] == test_user.name
