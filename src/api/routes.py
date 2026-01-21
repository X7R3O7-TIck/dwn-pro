"""API routes for the downloader service"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse
from datetime import datetime
from pathlib import Path
import urllib.parse

import sys
import os

# Calculate project root from this file's location
PROJECT_ROOT = Path(__file__).parent.parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

from core.downloader import SocialMediaDownloader
from core.url_detector import detect_platform, Platform
from .models import (
    DownloadRequest,
    BatchDownloadRequest,
    VideoInfoRequest,
    BatchVideoInfoRequest,
    DownloadResponse,
    VideoInfoResponse,
    HealthResponse,
    HistoryItem,
    HistoryResponse,
    QualityOptionResponse,
    ErrorResponse,
)


router = APIRouter()

# Global downloader instance
_downloader: Optional[SocialMediaDownloader] = None


def get_downloader() -> SocialMediaDownloader:
    """Get or create downloader instance"""
    global _downloader
    if _downloader is None:
        _downloader = SocialMediaDownloader()
    return _downloader


def get_file_url(request: Request, filename: str) -> str:
    """Generate full file URL for a downloaded file"""
    base_url = str(request.base_url).rstrip("/")
    return f"{base_url}/files/{urllib.parse.quote(filename)}"


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check API health status"""
    downloader = get_downloader()
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        supported_platforms=downloader.get_supported_platforms(),
        timestamp=datetime.now(),
    )


@router.get("/info", response_model=VideoInfoResponse, tags=["Info"])
async def get_video_info(url: str = Query(..., description="Video URL")):
    """
    Get video metadata information

    Returns title, duration, available qualities, and other metadata
    without downloading the video.
    """
    downloader = get_downloader()

    if not downloader.is_supported(url):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported URL. Supported platforms: {downloader.get_supported_platforms()}",
        )

    try:
        info = downloader.get_video_info(url)
        return VideoInfoResponse(
            url=info.url,
            platform=info.platform,
            title=info.title,
            description=info.description,
            thumbnail=info.thumbnail,
            duration=info.duration,
            uploader=info.uploader,
            upload_date=info.upload_date,
            view_count=info.view_count,
            available_qualities=info.available_qualities,
            available_formats=info.available_formats,
            is_live=info.is_live,
            error=info.error,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download", response_model=DownloadResponse, tags=["Download"])
async def download_video(request: DownloadRequest, http_request: Request = None):
    """
    Start a video download

    Returns a task ID that can be used to track progress.
    """
    downloader = get_downloader()

    if not downloader.is_supported(request.url):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported URL. Supported platforms: {downloader.get_supported_platforms()}",
        )

    try:
        result = downloader.download(
            url=request.url,
            quality=request.quality,
            format_name=request.format,
            output_path=request.output_path,
        )

        progress = downloader.get_download_progress(result.task_id)

        return DownloadResponse(
            task_id=result.task_id,
            status=progress.status.value if progress else "queued",
            url=result.url,
            platform=result.platform,
            title=result.title,
            progress_percent=progress.progress_percent if progress else 0.0,
            file_path=result.file_path,
            file_size=result.file_size,
            message=result.message,
            error=result.error,
            timestamp=result.timestamp,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/download/progress/{task_id}", response_model=DownloadResponse, tags=["Download"]
)
async def get_download_progress(task_id: str):
    """Get download progress for a task"""
    downloader = get_downloader()
    progress = downloader.get_download_progress(task_id)

    if progress is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return DownloadResponse(
        task_id=progress.task_id,
        status=progress.status.value,
        url=progress.url,
        platform=progress.platform,
        title=progress.title,
        progress_percent=progress.progress_percent,
        file_path=progress.file_path,
        file_size=progress.file_size,
        message=progress.message,
        error=progress.error,
        timestamp=progress.timestamp,
    )


@router.post("/download/batch", tags=["Download"])
async def batch_download(request: BatchDownloadRequest):
    """
    Start batch video downloads

    Returns a list of task IDs for tracking progress.
    """
    downloader = get_downloader()

    # Validate all URLs
    unsupported = [url for url in request.urls if not downloader.is_supported(url)]
    if unsupported:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported URLs found. Supported platforms: {downloader.get_supported_platforms()}",
        )

    try:
        results = downloader.download_batch(
            urls=request.urls,
            quality=request.quality,
            format_name=request.format,
            output_path=request.output_path,
            concurrent=request.concurrent,
        )

        task_ids = [r.task_id for r in results]
        return {
            "message": f"Started {len(results)} downloads",
            "task_ids": task_ids,
            "total": len(results),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/qualities", response_model=list[QualityOptionResponse], tags=["Quality"])
async def get_quality_options():
    """Get available quality options"""
    downloader = get_downloader()
    return downloader.get_quality_options()


@router.get(
    "/qualities/{url}", response_model=list[QualityOptionResponse], tags=["Quality"]
)
async def get_quality_options_for_url(url: str):
    """Get available quality options for a specific URL"""
    downloader = get_downloader()

    if not downloader.is_supported(url):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported URL. Supported platforms: {downloader.get_supported_platforms()}",
        )

    # Get platform-specific options
    platform = detect_platform(url)
    platform_specific_options = {
        "youtube": [
            "4k",
            "1080p",
            "720p",
            "480p",
            "360p",
            "best",
            "audio",
            "audio_mp3",
        ],
        "facebook": ["720p", "480p", "360p", "best", "audio"],
        "instagram": ["720p", "480p", "360p", "best", "audio"],
    }

    options = platform_specific_options.get(platform.value, ["best"])
    return [{"name": opt, "description": opt} for opt in options]


@router.get("/history", response_model=HistoryResponse, tags=["History"])
async def get_download_history():
    """Get download history"""
    downloader = get_downloader()
    history = downloader.get_download_history()

    items = [
        HistoryItem(
            task_id=item.task_id,
            url=item.url,
            platform=item.platform,
            title=item.title,
            file_path=item.file_path,
            file_size=item.file_size,
            success=item.success,
            timestamp=item.timestamp,
            error=item.error,
        )
        for item in history
    ]

    return HistoryResponse(items=items, total_count=len(items))


@router.delete("/history", tags=["History"])
async def clear_download_history():
    """Clear download history"""
    downloader = get_downloader()
    downloader.clear_history()
    return {"message": "History cleared"}


@router.delete("/history/{task_id}", tags=["History"])
async def delete_history_item(task_id: str):
    """Delete a specific history item"""
    downloader = get_downloader()
    progress = downloader.get_download_progress(task_id)

    if progress:
        downloader.progress_tracker.remove_task(task_id)
        return {"message": f"Task {task_id} removed"}

    raise HTTPException(status_code=404, detail="Task not found")


@router.get("/platforms", tags=["Info"])
async def get_supported_platforms():
    """Get list of supported platforms"""
    downloader = get_downloader()
    return {
        "platforms": downloader.get_supported_platforms(),
        "quality_options": downloader.get_quality_options(),
    }


@router.get("/files/{filename}", tags=["Files"])
async def serve_file(filename: str):
    """
    Download a file by filename

    Returns the actual file for download.
    """
    downloads_dir = PROJECT_ROOT / "downloads"
    file_path = downloads_dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Not a file")

    return FileResponse(
        path=str(file_path), filename=filename, media_type="application/octet-stream"
    )


@router.get("/files", tags=["Files"])
async def list_files():
    """
    List all downloaded files
    """
    downloads_dir = PROJECT_ROOT / "downloads"

    if not downloads_dir.exists():
        return {"files": [], "total": 0}

    files = []
    for f in downloads_dir.iterdir():
        if f.is_file():
            stat = f.stat()
            files.append(
                {
                    "name": f.name,
                    "size_bytes": stat.st_size,
                    "size_mb": round(stat.st_size / 1024 / 1024, 2),
                    "url": f"/files/{f.name}",
                    "download_url": f"/files/{f.name}",
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }
            )

    return {"files": files, "total": len(files), "downloads_dir": str(downloads_dir)}
