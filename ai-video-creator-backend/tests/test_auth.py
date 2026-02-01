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
    assert data["username"] == test_user.username
    assert data["name"] == test_user.name
    assert data["isActive"] == True  # camelCase from APIModel


@pytest.mark.asyncio
async def test_register_user(async_client: AsyncClient):
    """Test user registration."""
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123",
            "name": "New User",
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert data["name"] == "New User"
    assert data["isActive"] == True  # camelCase from APIModel
    assert "id" in data
