"""FastAPI application for Social Media Downloader"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

from .routes import router
from core.downloader import SocialMediaDownloader

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
DOWNLOADS_DIR = PROJECT_ROOT / "downloads"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    print("Starting Social Media Downloader API...")
    print(f"Downloads directory: {DOWNLOADS_DIR}")

    # Ensure downloads directory exists
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

    yield
    # Shutdown
    print("Shutting down Social Media Downloader API...")


# Create FastAPI app
app = FastAPI(
    title="Social Media Downloader API",
    description="Download videos from YouTube, Facebook, and Instagram",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory for serving downloads
if DOWNLOADS_DIR.exists():
    app.mount("/files", StaticFiles(directory=str(DOWNLOADS_DIR)), name="files")
    print(f"Static files mounted at /files -> {DOWNLOADS_DIR}")

# Include API routes
app.include_router(router, prefix="/api")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "name": "Social Media Downloader API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
        },
    )


def create_app() -> FastAPI:
    """Create and configure FastAPI app"""
    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
