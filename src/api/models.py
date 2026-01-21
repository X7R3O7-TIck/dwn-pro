"""Pydantic models for API"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class DownloadRequest(BaseModel):
    """Request model for downloading videos"""
    url: str = Field(..., description="Video URL to download")
    quality: str = Field(default="best", description="Quality preset (best, 720p, 480p, etc.)")
    format: str = Field(default="mp4", description="Output format (mp4, mkv, etc.)")
    audio_only: bool = Field(default=False, description="Extract audio only")
    output_path: Optional[str] = Field(default=None, description="Custom output directory")
    callback_url: Optional[str] = Field(default=None, description="Webhook callback URL")


class BatchDownloadRequest(BaseModel):
    """Request model for batch downloads"""
    urls: List[str] = Field(..., description="List of video URLs")
    quality: str = Field(default="best", description="Quality preset")
    format: str = Field(default="mp4", description="Output format")
    output_path: Optional[str] = Field(default=None, description="Custom output directory")
    concurrent: bool = Field(default=True, description="Download concurrently")


class VideoInfoRequest(BaseModel):
    """Request model for getting video info"""
    url: str = Field(..., description="Video URL")


class BatchVideoInfoRequest(BaseModel):
    """Request model for batch video info"""
    urls: List[str] = Field(..., description="List of video URLs")


class DownloadResponse(BaseModel):
    """Response model for download"""
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Download status (queued, downloading, completed, failed)")
    url: str = Field(..., description="Original video URL")
    platform: str = Field(..., description="Platform name")
    title: Optional[str] = Field(default=None, description="Video title")
    progress_percent: float = Field(default=0.0, description="Download progress percentage")
    file_path: Optional[str] = Field(default=None, description="Path to downloaded file")
    file_size: Optional[int] = Field(default=None, description="File size in bytes")
    message: str = Field(default="", description="Status message")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp")


class VideoInfoResponse(BaseModel):
    """Response model for video info"""
    url: str = Field(..., description="Video URL")
    platform: str = Field(..., description="Platform name")
    title: Optional[str] = Field(default=None, description="Video title")
    description: Optional[str] = Field(default=None, description="Video description")
    thumbnail: Optional[str] = Field(default=None, description="Thumbnail URL")
    duration: Optional[int] = Field(default=None, description="Duration in seconds")
    uploader: Optional[str] = Field(default=None, description="Uploader name")
    upload_date: Optional[str] = Field(default=None, description="Upload date")
    view_count: Optional[int] = Field(default=None, description="View count")
    available_qualities: List[str] = Field(default_factory=list, description="Available quality options")
    available_formats: List[Dict[str, Any]] = Field(default_factory=list, description="Available formats")
    is_live: bool = Field(default=False, description="Is live stream")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="API status")
    version: str = Field(..., description="Version string")
    supported_platforms: List[str] = Field(..., description="Supported platforms")
    timestamp: datetime = Field(default_factory=datetime.now)


class QualityOptionResponse(BaseModel):
    """Response model for quality options"""
    name: str = Field(..., description="Quality name")
    description: str = Field(..., description="Quality description")
    max_height: Optional[int] = Field(default=None, description="Maximum video height")
    is_audio_only: bool = Field(default=False, description="Is audio only")


class HistoryItem(BaseModel):
    """Download history item"""
    task_id: str
    url: str
    platform: str
    title: Optional[str]
    file_path: Optional[str]
    file_size: Optional[int]
    success: bool
    timestamp: datetime
    error: Optional[str] = None


class HistoryResponse(BaseModel):
    """Response model for download history"""
    items: List[HistoryItem]
    total_count: int


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.now)
