"""Test wizard turns."""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_wizard_turn_with_ui_event():
    """Test wizard turn with UI event."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Start session
        start_response = await client.post(
            "/v1/sessions/start",
            headers={
                "X-Tenant-Id": "boom",
                "X-Api-Key": "API_KEY_123"
            },
            json={"context": {}, "consent": {}}
        )
        session_id = start_response.json()["session_id"]
        
        # Send turn
        turn_response = await client.post(
            "/v1/wizard/turn",
            headers={
                "X-Tenant-Id": "boom",
                "X-Api-Key": "API_KEY_123"
            },
            json={
                "session_id": session_id,
                "event_id": "evt_123",
                "ui_event": {
                    "type": "selected_option",
                    "field": "industry",
                    "value": "ecommerce"
                }
            }
        )
        
        assert turn_response.status_code == 200
        data = turn_response.json()
        assert "assistant_message" in data
        assert "wizard" in data


@pytest.mark.asyncio
async def test_wizard_idempotency():
    """Test idempotency of wizard turns."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Start session
        start_response = await client.post(
            "/v1/sessions/start",
            headers={
                "X-Tenant-Id": "boom",
                "X-Api-Key": "API_KEY_123"
            },
            json={"context": {}, "consent": {}}
        )
        session_id = start_response.json()["session_id"]
        
        # Send same event twice
        event_data = {
            "session_id": session_id,
            "event_id": "evt_same",
            "ui_event": {
                "type": "selected_option",
                "field": "industry",
                "value": "ecommerce"
            }
        }
        
        response1 = await client.post(
            "/v1/wizard/turn",
            headers={
                "X-Tenant-Id": "boom",
                "X-Api-Key": "API_KEY_123"
            },
            json=event_data
        )
        
        response2 = await client.post(
            "/v1/wizard/turn",
            headers={
                "X-Tenant-Id": "boom",
                "X-Api-Key": "API_KEY_123"
            },
            json=event_data
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json() == response2.json()
