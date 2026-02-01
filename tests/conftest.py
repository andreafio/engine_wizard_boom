"""Test configuration."""
import pytest
from app.storage.redis_store import redis_store


@pytest.fixture
async def redis_connection():
    """Redis connection fixture for async tests that need it."""
    await redis_store.connect()
    yield redis_store
    await redis_store.disconnect()
