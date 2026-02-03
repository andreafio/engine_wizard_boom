"""FastAPI application main entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.storage.redis_store import redis_store
from app.api import routes_sessions, routes_wizard

# Configure logging
configure_logging()
logger = get_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Application lifespan manager."""
#     try:
#         # Startup
#         logger.info("application_starting", env=settings.app_env)
        
#         # Connect to Redis
#         await redis_store.connect()
        
#         yield
        
#         # Shutdown
#         logger.info("application_stopping")
#         await redis_store.disconnect()
#     except Exception as e:
#         logger.error("lifespan_error", error=str(e))
#         raise


# Create FastAPI app
app = FastAPI(
    title="BOOM Wizard Engine",
    description="Strategic marketing wizard backend",
    version="1.0.0",
    # lifespan=lifespan
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "null"],  # Allow null origin for local file testing
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
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "env": settings.app_env,
        "timestamp": "2026-02-02"
    }


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
