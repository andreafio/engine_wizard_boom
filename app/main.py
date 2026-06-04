"""FastAPI application main entry point."""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from sqlalchemy import text

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.storage.redis_store import redis_store
from app.db.database import init_db, get_engine
from app.api import routes_sessions, routes_wizard

# Configure logging
configure_logging()
logger = get_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("application_starting", env=settings.app_env)
    try:
        await redis_store.connect()
    except Exception as e:
        logger.warning("redis_startup_failed", error=str(e),
                       message="Falling back to in-memory storage")
    await init_db()

    yield

    logger.info("application_stopping")
    await redis_store.disconnect()


# Create FastAPI app
app = FastAPI(
    title="BOOM Wizard Engine",
    description="Strategic marketing wizard backend",
    version="1.0.0",
    lifespan=lifespan,
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error("unhandled_exception", 
                 path=request.url.path,
                 error=str(exc),
                 exc_type=type(exc).__name__)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc) if not settings.is_production else "An error occurred"
        }
    )


# Health check
@app.get("/health")
async def health_check():
    checks = {}
    overall = "healthy"

    # Redis
    if redis_store.redis is not None:
        try:
            await redis_store.redis.ping()
            checks["redis"] = {"status": "ok", "mode": "redis"}
        except Exception as e:
            checks["redis"] = {"status": "error", "error": str(e)}
            overall = "unhealthy"
    else:
        checks["redis"] = {"status": "ok", "mode": "memory"}

    # Database
    engine = get_engine()
    if engine is not None:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            checks["db"] = {"status": "ok"}
        except Exception as e:
            checks["db"] = {"status": "error", "error": str(e)}
            overall = "unhealthy"
    else:
        checks["db"] = {"status": "disabled"}

    return JSONResponse(
        status_code=status.HTTP_200_OK if overall == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": overall,
            "version": "1.0.0",
            "env": settings.app_env,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": checks,
        }
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "BOOM Wizard Engine",
        "version": "1.0.0",
        "docs": "/docs"
    }


# Include routers
app.include_router(routes_sessions.router)
app.include_router(routes_wizard.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.app_env == "dev",
        log_level=settings.log_level.lower()
    )
