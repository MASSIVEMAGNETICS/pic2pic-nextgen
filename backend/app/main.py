"""
pic2pic-nextgen Backend
=======================
FastAPI application entry point.

Production-ready backend with:
- REST API for image upload and processing
- WebSocket for real-time preview streaming
- Self-healing watchdog system
- OpenAPI documentation
"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.routes import router as api_router
from .api.websocket import router as ws_router, get_watchdog
from .config import settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting pic2pic-nextgen v{settings.app_version}")
    logger.info(f"Deployment tier: {settings.deployment_tier.value}")

    # Create required directories
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.checkpoint_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.holo_presets_dir).mkdir(parents=True, exist_ok=True)

    # Start self-healing watchdog
    watchdog = get_watchdog()
    await watchdog.start()

    yield

    # Shutdown
    logger.info("Shutting down pic2pic-nextgen")
    await watchdog.stop()


# Create FastAPI app
app = FastAPI(
    title="pic2pic-nextgen",
    description="""
    Holographic Reconstruction Engine API

    ## Features
    - **Image Upload**: Drag & drop or paste images for instant holographic reconstruction
    - **Live Preview**: Real-time streaming preview with liquid-time gating visualization
    - **Batch Processing**: Process multiple images in background with progress tracking
    - **Memory Banks**: Save and load .holo memory banks with trained patterns
    - **Dev Mode**: Full parameter exposure for advanced users (hidden by default)

    ## WebSocket
    Connect to `/ws` for real-time communication with live preview streaming.
    """,
    version=settings.app_version,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix="/api/v1", tags=["API"])
app.include_router(ws_router, tags=["WebSocket"])


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "deployment_tier": settings.deployment_tier.value,
        "docs": "/docs",
        "websocket": "/ws",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler with self-healing integration."""
    logger.error(f"Unhandled exception: {exc}")

    # Notify watchdog of error
    watchdog = get_watchdog()
    watchdog.handle_error(exc)

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.debug else "An error occurred",
        },
    )


def main():
    """Run the application with uvicorn."""
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )


if __name__ == "__main__":
    main()
