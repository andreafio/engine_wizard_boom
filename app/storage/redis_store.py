"""Redis storage for sessions."""
import json
from typing import Dict, Optional
import redis.asyncio as redis
from app.core.config import settings
from app.core.logging import get_logger
from app.wizard.state import Session

logger = get_logger(__name__)


class RedisStore:
    """Redis-based session storage."""
    
    def __init__(self):
        """Initialize Redis connection."""
        self.redis: Optional[redis.Redis] = None
        self.memory_store: Dict[str, str] = {}  # In-memory storage for testing
    
    async def connect(self):
        """Connect to Redis or use in-memory storage."""
        if settings.redis_url == "memory://":
            # Use in-memory storage for testing
            self.redis = None
            logger.info("using_in_memory_storage")
        else:
            try:
                self.redis = await redis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                await self.redis.ping()
                logger.info("redis_connected", url=settings.redis_url)
            except Exception as e:
                self.redis = None  # fallback in-memory
                logger.error("redis_connection_failed", error=str(e))
                raise
    
    async def ensure_connected(self):
        """Lazy connect: no-op if already connected or using in-memory mode."""
        if self.redis is not None or settings.redis_url == "memory://":
            return
        await self.connect()

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            logger.info("redis_disconnected")
        else:
            logger.info("memory_storage_disconnected")

    def _session_key(self, session_id: str) -> str:
        """Generate Redis key for session."""
        return f"session:{session_id}"
    
    async def save_session(self, session: Session) -> bool:
        """Save session to Redis or memory.
        
        Args:
            session: Session to save
            
        Returns:
            True if saved successfully
        """
        await self.ensure_connected()
        try:
            key = self._session_key(session.session_id)
            data = session.model_dump_json()
            
            if self.redis:
                await self.redis.setex(
                    key,
                    settings.session_ttl_seconds,
                    data
                )
            else:
                # Use in-memory storage
                self.memory_store[key] = data
            
            logger.debug("session_saved", session_id=session.session_id)
            return True
        except Exception as e:
            logger.error("session_save_failed", session_id=session.session_id, error=str(e))
            return False
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve session from Redis or memory.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session object or None if not found
        """
        await self.ensure_connected()
        try:
            key = self._session_key(session_id)

            if self.redis:
                data = await self.redis.get(key)
            else:
                data = self.memory_store.get(key)
            
            if not data:
                logger.debug("session_not_found", session_id=session_id)
                return None
            
            session = Session.model_validate_json(data)
            logger.debug("session_retrieved", session_id=session_id)
            return session
        except Exception as e:
            logger.error("session_get_failed", session_id=session_id, error=str(e))
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session from Redis.

        Args:
            session_id: Session ID

        Returns:
            True if deleted
        """
        await self.ensure_connected()
        try:
            key = self._session_key(session_id)
            if self.redis:
                await self.redis.delete(key)
            else:
                self.memory_store.pop(key, None)
            logger.debug("session_deleted", session_id=session_id)
            return True
        except Exception as e:
            logger.error("session_delete_failed", session_id=session_id, error=str(e))
            return False

    async def extend_session(self, session_id: str) -> bool:
        """Extend session TTL.

        Args:
            session_id: Session ID

        Returns:
            True if extended
        """
        await self.ensure_connected()
        try:
            key = self._session_key(session_id)
            if self.redis:
                await self.redis.expire(key, settings.session_ttl_seconds)
            # In memory-mode TTL is not enforced (acceptable for dev/test)
            return True
        except Exception as e:
            logger.error("session_extend_failed", session_id=session_id, error=str(e))
            return False


    def _idempotent_key(self, event_id: str) -> str:
        """Generate Redis key for idempotency cache."""
        return f"idempotent:{event_id}"

    async def get_idempotent(self, event_id: str) -> Optional[dict]:
        """Get cached result for idempotency check (TTL: 24h)."""
        await self.ensure_connected()
        try:
            key = self._idempotent_key(event_id)
            data = await self.redis.get(key) if self.redis else self.memory_store.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error("idempotent_get_failed", event_id=event_id, error=str(e))
            return None

    async def put_idempotent(self, event_id: str, result: dict) -> None:
        """Cache result for idempotency (TTL: 24h)."""
        await self.ensure_connected()
        try:
            key = self._idempotent_key(event_id)
            data = json.dumps(result, default=str)
            if self.redis:
                await self.redis.setex(key, 86400, data)
            else:
                self.memory_store[key] = data
        except Exception as e:
            logger.error("idempotent_put_failed", event_id=event_id, error=str(e))


# Global store instance
redis_store = RedisStore()
