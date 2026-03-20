import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_register():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "test123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_login():
    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "test123"}
        )
        response = await client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "test123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
