"""Test session management."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_start_session():
    """Test starting a new session."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/sessions/start",
            headers={
                "X-Tenant-Id": "boom",
                "X-Api-Key": "API_KEY_123"
            },
            json={
                "context": {"page_url": "https://example.com"},
                "consent": {"gdpr": True}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["session_id"].startswith("sess_")
        assert "wizard" in data
        assert data["wizard"]["current_step"] == "context"


@pytest.mark.asyncio
async def test_start_session_unauthorized():
    """Test unauthorized access."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/sessions/start",
            headers={
                "X-Tenant-Id": "unknown",
                "X-Api-Key": "wrong_key"
            },
            json={}
        )
        
        assert response.status_code == 401
