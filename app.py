#!/usr/bin/env python3
"""
Social Media Downloader - Complete Server Application

Features:
- Full API access for YouTube, Facebook, Instagram downloads
- Unique content ID generation (NOT title-based)
- Global file serving via URL
- Beautiful Web UI for downloads
- Auto-install dependencies on first run
- Installed via pyproject.toml
"""

import sys
import os
import json
import time
import uuid
import subprocess
import warnings
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

# Suppress pip warnings
warnings.filterwarnings("ignore", category=UserWarning)
os.environ["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"

# Add project to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# DEPENDENCY CHECK (for non-pip installation)
# ============================================================================

REQUIRED_PACKAGES = {
    "fastapi": "fastapi",
    "uvicorn": "uvicorn", 
    "jinja2": "jinja2",
    "python-multipart": "python_multipart",
    "yt-dlp": "yt_dlp",
    "requests": "requests",
    "pydantic": "pydantic",
    "httpx": "httpx",
}


def check_and_install_dependencies():
    """Check and install required dependencies (fallback for non-pip install)"""
    print("=" * 70)
    print("SOCIAL MEDIA DOWNLOADER - DEPENDENCY CHECK")
    print("=" * 70)
    
    missing_packages = []
    installed_packages = []
    
    for package_name, import_name in REQUIRED_PACKAGES.items():
        try:
            __import__(import_name)
            version = getattr(sys.modules[import_name], "__version__", "unknown")
            installed_packages.append(f"  [OK] {package_name} ({version})")
        except ImportError:
            missing_packages.append(package_name)
            print(f"  [MISSING] {package_name}")
    
    if installed_packages:
        print("\nInstalled Packages:")
        for pkg in installed_packages:
            print(pkg)
    
    if missing_packages:
        print(f"\nMissing Packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        
        try:
            for package in missing_packages:
                print(f"  Installing {package}...")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--quiet", package],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    print(f"  Failed to install {package}: {result.stderr}")
                    return False
                
            print("\n[OK] All dependencies installed successfully!")
            
        except subprocess.SubprocessError as e:
            print(f"\n[ERROR] Failed to install dependencies: {e}")
            print("Please install via pip: pip install -e .")
            return False
    
    print("\n[OK] All dependencies are satisfied!")
    return True


def check_ffmpeg():
    """Check if FFmpeg is installed"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            version = result.stdout.split("\n")[0]
            print(f"  [OK] FFmpeg: {version.split()[2]}")
            return True
    except (FileNotFoundError, subprocess.SubprocessError):
        pass
    
    print("  [WARNING] FFmpeg not found (audio extraction may not work)")
    print("    Install: sudo apt install ffmpeg  (Ubuntu/Debian)")
    print("    Or: brew install ffmpeg  (macOS)")
    return False


# Run dependency check (only if not installed via pip)
if not os.path.exists(PROJECT_ROOT / "pyproject.toml"):
    if not check_and_install_dependencies():
        sys.exit(1)
    
    check_ffmpeg()
    
    print("\n" + "=" * 70)
    print("Starting Social Media Downloader...")
    print("=" * 70 + "\n")

# Now import after dependency check
from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from src.core.downloader import SocialMediaDownloader
from src.core.url_detector import detect_platform


# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Server configuration"""
    HOST = "0.0.0.0"
    PORT = 8000
    DEBUG = False
    DOWNLOADS_DIR = PROJECT_ROOT / "downloads"
    MAX_CONCURRENT_DOWNLOADS = 3
    SUPPORTED_PLATFORMS = ["youtube", "facebook", "instagram"]


# ============================================================================
# APP INITIALIZATION
# ============================================================================

app = FastAPI(
    title="Social Media Downloader",
    description="Download videos from YouTube, Facebook, Instagram with unique IDs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure downloads directory exists
Config.DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Mount static files for serving downloads
app.mount("/files", StaticFiles(directory=str(Config.DOWNLOADS_DIR)), name="files")

# Templates
TEMPLATES_DIR = PROJECT_ROOT / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Initialize downloader
downloader = SocialMediaDownloader(output_dir=str(Config.DOWNLOADS_DIR))


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_content_id(platform: str = "content") -> str:
    """Generate unique content ID"""
    timestamp = int(time.time())
    unique_hash = hash(f"{timestamp}_{uuid.uuid4()}") % 10000
    return f"{platform}_{timestamp}_{unique_hash}"


def get_file_info(file_path: Path) -> Optional[Dict[str, Any]]:
    """Get file information"""
    if not file_path.exists() or not file_path.is_file():
        return None
    
    stat = file_path.stat()
    return {
        "name": file_path.name,
        "path": str(file_path),
        "size_bytes": stat.st_size,
        "size_mb": round(stat.st_size / 1024 / 1024, 2),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "download_url": f"/files/{file_path.name}",
        "content_id": file_path.stem
    }


def get_all_downloads() -> List[Dict[str, Any]]:
    """Get all downloaded files"""
    files = []
    if Config.DOWNLOADS_DIR.exists():
        for f in sorted(Config.DOWNLOADS_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.is_file():
                info = get_file_info(f)
                if info:
                    files.append(info)
    return files


# ============================================================================
# API ROUTES
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def home():
    """Home page"""
    return templates.TemplateResponse("index.html", {"request": {}})


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "supported_platforms": Config.SUPPORTED_PLATFORMS,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/info")
async def get_video_info(url: str):
    """Get video information"""
    if not downloader.is_supported(url):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported URL. Supported platforms: {Config.SUPPORTED_PLATFORMS}"
        )
    
    platform = detect_platform(url)
    content_id = generate_content_id(platform.value)
    
    try:
        info = downloader.get_video_info(url)
        return {
            "content_id": content_id,
            "user_link": url,
            "platform": info.platform,
            "title": info.title,
            "description": info.description,
            "thumbnail": info.thumbnail,
            "duration": info.duration,
            "duration_formatted": f"{info.duration // 60}:{info.duration % 60:02d}" if info.duration else None,
            "uploader": info.uploader,
            "upload_date": info.upload_date,
            "view_count": info.view_count,
            "available_qualities": info.available_qualities,
            "is_live": info.is_live,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/download")
async def download_video(
    url: str = Form(...),
    quality: str = Form("best"),
    format_name: str = Form("mp4")
):
    """Download a video with unique content ID as filename"""
    if not downloader.is_supported(url):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported URL. Supported platforms: {Config.SUPPORTED_PLATFORMS}"
        )
    
    platform = detect_platform(url)
    content_id = generate_content_id(platform.value)
    
    try:
        info = downloader.get_video_info(url)
        
        # Use content ID as filename
        unique_filename = f"{content_id}.%(ext)s"
        output_template = str(Config.DOWNLOADS_DIR / unique_filename)
        
        result = downloader.download(
            url=url,
            quality=quality,
            format_name=format_name,
            output_path=str(Config.DOWNLOADS_DIR),
            outtmpl=output_template
        )
        
        file_path = result.file_path
        file_size = result.file_size
        file_name = Path(file_path).name if file_path else None
        
        return {
            "content_id": content_id,
            "user_link": url,
            "task_id": result.task_id,
            "platform": result.platform,
            "video_title": result.title,
            "file_name": file_name,
            "file_path": file_path,
            "file_size_mb": round(file_size / 1024 / 1024, 2) if file_size else None,
            "file_url": f"/files/{file_name}" if file_name else None,
            "global_url": f"http://{Config.HOST}:{Config.PORT}/files/{file_name}" if file_name else None,
            "download_status": "completed" if result.success else "failed",
            "error": result.error,
            "message": result.message,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/progress/{task_id}")
async def get_download_progress(task_id: str):
    """Get download progress"""
    progress = downloader.get_download_progress(task_id)
    
    if progress is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": progress.task_id,
        "status": progress.status.value,
        "url": progress.url,
        "platform": progress.platform,
        "title": progress.title,
        "progress_percent": progress.progress_percent,
        "downloaded_bytes": progress.downloaded_bytes,
        "total_bytes": progress.total_bytes,
        "speed": progress.speed,
        "eta": progress.eta,
        "file_path": progress.file_path,
        "file_size": progress.file_size,
        "message": progress.message,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/files")
async def list_files():
    """List all downloaded files"""
    files = get_all_downloads()
    return {
        "files": files,
        "total": len(files),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/files/{filename}")
async def serve_file(filename: str):
    """Serve a file for download"""
    file_path = Config.DOWNLOADS_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Not a file")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream"
    )


@app.delete("/api/files/{filename}")
async def delete_file(filename: str):
    """Delete a downloaded file"""
    file_path = Config.DOWNLOADS_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        file_path.unlink()
        return {
            "message": f"File {filename} deleted",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history")
async def get_download_history():
    """Get download history"""
    history = downloader.get_download_history()
    return {
        "items": [
            {
                "content_id": f"history_{item.task_id}",
                "task_id": item.task_id,
                "url": item.url,
                "platform": item.platform,
                "title": item.title,
                "file_path": item.file_path,
                "file_name": Path(item.file_path).name if item.file_path else None,
                "file_size_mb": round(item.file_size / 1024 / 1024, 2) if item.file_size else None,
                "success": item.success,
                "error": item.error,
                "timestamp": item.timestamp.isoformat()
            }
            for item in history
        ],
        "total_count": len(history),
        "timestamp": datetime.now().isoformat()
    }


@app.delete("/api/history")
async def clear_history():
    """Clear download history"""
    downloader.clear_history()
    return {
        "message": "History cleared",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/qualities")
async def get_quality_options():
    """Get available quality options"""
    return downloader.get_quality_options()


@app.get("/api/platforms")
async def get_platforms():
    """Get supported platforms"""
    return {
        "platforms": Config.SUPPORTED_PLATFORMS,
        "quality_options": downloader.get_quality_options()
    }


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point"""
    print("=" * 70)
    print("SOCIAL MEDIA DOWNLOADER - SERVER")
    print("=" * 70)
    print(f"Host: {Config.HOST}")
    print(f"Port: {Config.PORT}")
    print(f"Downloads: {Config.DOWNLOADS_DIR}")
    print(f"API Docs: http://{Config.HOST}:{Config.PORT}/docs")
    print(f"Web UI: http://{Config.HOST}:{Config.PORT}/")
    print("=" * 70)
    print("\nPress Ctrl+C to stop the server\n")
    
    uvicorn.run(
        "app:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG
    )


if __name__ == "__main__":
    main()
