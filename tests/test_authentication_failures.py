# tests/test_authentication_failures.py
import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
async def test_age_groups_unauthorized():
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/age-groups/")
    assert response.status_code == 401
    assert "Not authenticated" in response.text


@pytest.mark.asyncio
async def test_enrollments_unauthorized():
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/enrollments/")
    assert response.status_code == 401
    assert "Not authenticated" in response.text
