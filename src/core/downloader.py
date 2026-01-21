"""Main downloader module"""

import os
import uuid
import yt_dlp
import concurrent.futures
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from threading import Lock

from .url_detector import detect_platform, Platform
from .quality_manager import QualityManager
from .progress_tracker import (
    ProgressTracker,
    DownloadProgress,
    DownloadStatus,
)


@dataclass
class DownloadResult:
    """Result of a download operation"""

    task_id: str
    success: bool
    url: str
    platform: str
    title: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_format: Optional[str] = None
    duration: Optional[int] = None
    uploader: Optional[str] = None
    thumbnail: Optional[str] = None
    view_count: Optional[int] = None
    error: Optional[str] = None
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "task_id": self.task_id,
            "success": self.success,
            "url": self.url,
            "platform": self.platform,
            "title": self.title,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_format": self.file_format,
            "duration": self.duration,
            "uploader": self.uploader,
            "thumbnail": self.thumbnail,
            "view_count": self.view_count,
            "error": self.error,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class VideoInfo:
    """Video metadata information"""

    url: str
    platform: str
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    duration: Optional[int] = None
    uploader: Optional[str] = None
    upload_date: Optional[str] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    available_formats: List[Dict] = field(default_factory=list)
    available_qualities: List[str] = field(default_factory=list)
    is_live: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "url": self.url,
            "platform": self.platform,
            "title": self.title,
            "description": self.description,
            "thumbnail": self.thumbnail,
            "duration": self.duration,
            "uploader": self.uploader,
            "upload_date": self.upload_date,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "available_formats": self.available_formats,
            "available_qualities": self.available_qualities,
            "is_live": self.is_live,
            "error": self.error,
        }


class SocialMediaDownloader:
    """
    Main downloader class for social media platforms

    Supports YouTube, Facebook, and Instagram video downloads
    with quality selection and progress tracking.
    """

    def __init__(
        self,
        output_dir: str = "./downloads",
        default_quality: str = "best",
        default_format: str = "mp4",
        progress_tracker: Optional[ProgressTracker] = None,
    ):
        """
        Initialize the downloader

        Args:
            output_dir: Default directory for downloads
            default_quality: Default quality preset
            default_format: Default output format
            progress_tracker: Optional custom progress tracker
        """
        self.output_dir = Path(output_dir)
        self.default_quality = default_quality
        self.default_format = default_format
        self.quality_manager = QualityManager()
        self.progress_tracker = progress_tracker or ProgressTracker()
        self.download_history: List[DownloadResult] = []

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _generate_task_id(self) -> str:
        """Generate unique task ID"""
        return str(uuid.uuid4())[:8]

    def _get_ydl_options(self, is_download: bool = False) -> Dict[str, Any]:
        """
        Get yt-dlp options with anti-bot measures

        Args:
            is_download: Whether this is for actual download (vs info extraction)

        Returns:
            Options dictionary for yt-dlp
        """
        options: Dict[str, Any] = {
            # Anti-bot measures
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "geo_bypass": True,
            "geo_bypass_country": "US",
            "no_color": True,
            "compat_opts": ["no-youtube-unavailable-videos"],
            "extractor_retries": 3,
            "fragment_retries": 3,
            "skip_unavailable_fragments": False,
            "concurrent_fragment_downloads": 1,
            # User agent (common browser)
            "http_header": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            },
        }

        if is_download:
            options.update(
                {
                    "outtmpl": str(self.output_dir / "%(id)s.%(ext)s"),
                    "merge_output_format": "mp4",
                    "postprocessors": [
                        {
                            "key": "FFmpegMerger",
                        }
                    ],
                }
            )

        return options

    def _extract_info(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Extract video information without downloading

        Args:
            url: Video URL
            **kwargs: Additional options

        Returns:
            Video info dictionary
        """
        options = self._get_ydl_options(is_download=False)
        options.update(kwargs)

        with yt_dlp.YoutubeDL(options) as ydl:
            try:
                info: Dict[str, Any] = ydl.extract_info(url, download=False)
                return info
            except Exception as e:
                # Try with cookies from browser if first attempt fails
                if "Sign in to confirm" in str(e) or "bot" in str(e).lower():
                    try:
                        # Try with Firefox cookies
                        options["cookies_from_browser"] = "firefox"
                        options["quiet"] = True
                        with yt_dlp.YoutubeDL(options) as ydl2:
                            info = ydl2.extract_info(url, download=False)
                            return info
                    except:
                        pass

                    try:
                        # Try with Chrome cookies
                        options["cookies_from_browser"] = "chrome"
                        with yt_dlp.YoutubeDL(options) as ydl2:
                            info = ydl2.extract_info(url, download=False)
                            return info
                    except:
                        pass

                    try:
                        # Try without cookies but with different user agent
                        options.pop("cookies_from_browser", None)
                        options["user_agent"] = (
                            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
                        )
                        with yt_dlp.YoutubeDL(options) as ydl2:
                            info = ydl2.extract_info(url, download=False)
                            return info
                    except:
                        pass

                raise Exception(f"Failed to extract info: {str(e)}")

    def get_video_info(self, url: str) -> VideoInfo:
        """
        Get video metadata information

        Args:
            url: Video URL

        Returns:
            VideoInfo object with metadata
        """
        platform = detect_platform(url)

        try:
            info = self._extract_info(url)

            # Extract available formats
            available_formats = []
            if "formats" in info:
                for f in info["formats"][:15]:  # Limit to first 15 formats
                    available_formats.append(
                        {
                            "format_id": f.get("format_id"),
                            "ext": f.get("ext"),
                            "resolution": f.get("resolution"),
                            "format_note": f.get("format_note"),
                            "filesize": f.get("filesize"),
                        }
                    )

            return VideoInfo(
                url=url,
                platform=platform.value,
                title=info.get("title"),
                description=info.get("description"),
                thumbnail=info.get("thumbnail"),
                duration=info.get("duration"),
                uploader=info.get("uploader"),
                upload_date=info.get("upload_date"),
                view_count=info.get("view_count"),
                like_count=info.get("like_count"),
                available_formats=available_formats,
                available_qualities=self.quality_manager.get_available_qualities(),
                is_live=info.get("is_live", False),
            )

        except Exception as e:
            return VideoInfo(
                url=url,
                platform=platform.value,
                error=str(e),
            )

    def download(
        self,
        url: str,
        quality: Optional[str] = None,
        format_name: Optional[str] = None,
        output_path: Optional[str] = None,
        output_template: Optional[str] = None,
        **kwargs,
    ) -> DownloadResult:
        """
        Download a video from URL

        Args:
            url: Video URL
            quality: Quality preset (default: from config)
            format_name: Output format (default: from config)
            output_path: Custom output directory
            output_template: Custom filename template
            **kwargs: Additional yt-dlp options

        Returns:
            DownloadResult object
        """
        task_id = self._generate_task_id()
        platform = detect_platform(url)

        # Create task in progress tracker
        self.progress_tracker.create_task(task_id, url, platform.value)

        # Use defaults if not specified
        quality = quality or self.default_quality
        format_name = format_name or self.default_format
        output_path = output_path or str(self.output_dir)

        # Ensure output directory exists
        Path(output_path).mkdir(parents=True, exist_ok=True)

        # Build output template
        if output_template is None:
            output_template = os.path.join(output_path, "%(title)s.%(ext)s")

        # Build download options with anti-bot measures
        options = self._get_ydl_options(is_download=True)

        # Add quality-specific options
        quality_options = self.quality_manager.build_download_options(
            quality=quality, format_name=format_name, output_template=output_template, **kwargs
        )
        options.update(quality_options)

        # Add progress hook
        progress_hook = self.progress_tracker.create_yt_dlp_hook(task_id)
        options["progress_hooks"] = [progress_hook]

        # Update status to downloading
        self.progress_tracker.update_progress(
            task_id,
            status=DownloadStatus.DOWNLOADING,
            message="Starting download...",
        )

        try:
            # First, extract info
            info = self._extract_info(url)
            title = info.get("title", "video")

            self.progress_tracker.update_progress(
                task_id,
                title=title,
                message=f"Downloading: {title}",
            )

            # Download the video
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])

            # Find the downloaded file
            file_path = None
            file_size = None
            file_format = format_name

            # Look for downloaded file
            downloaded_file = Path(output_path)
            expected_pattern = f"{title}."

            for f in downloaded_file.glob(f"{title}.*"):
                file_path = str(f)
                file_size = f.stat().st_size if f.exists() else None
                file_format = f.suffix[1:] if f.suffix else format_name
                break

            # If file not found with exact title, find any recent file
            if not file_path:
                for f in sorted(
                    downloaded_file.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True
                )[:1]:
                    if f.is_file() and not f.name.startswith("."):
                        file_path = str(f)
                        file_size = f.stat().st_size

            # Mark as complete
            self.progress_tracker.set_complete(
                task_id,
                file_path=file_path,
                file_size=file_size,
                message="Download completed successfully",
                title=title,
            )

            result = DownloadResult(
                task_id=task_id,
                success=True,
                url=url,
                platform=platform.value,
                title=title,
                file_path=file_path,
                file_size=file_size,
                file_format=file_format,
                duration=info.get("duration"),
                uploader=info.get("uploader"),
                thumbnail=info.get("thumbnail"),
                view_count=info.get("view_count"),
                message="Download completed successfully",
            )

            self.download_history.append(result)
            return result

        except Exception as e:
            error_msg = str(e)
            self.progress_tracker.set_failed(task_id, error_msg)

            result = DownloadResult(
                task_id=task_id,
                success=False,
                url=url,
                platform=platform.value,
                error=error_msg,
                message=f"Download failed: {error_msg}",
            )

            self.download_history.append(result)
            return result

    def download_batch(
        self,
        urls: List[str],
        quality: Optional[str] = None,
        format_name: Optional[str] = None,
        output_path: Optional[str] = None,
        concurrent: bool = True,
        max_concurrent: int = 3,
        **kwargs,
    ) -> List[DownloadResult]:
        """
        Download multiple videos

        Args:
            urls: List of video URLs
            quality: Quality preset
            format_name: Output format
            output_path: Output directory
            concurrent: Whether to download concurrently
            max_concurrent: Maximum concurrent downloads
            **kwargs: Additional options

        Returns:
            List of DownloadResult objects
        """
        results = []

        if concurrent and len(urls) > 1:
            lock = Lock()

            def download_one(url):
                result = self.download(
                    url=url,
                    quality=quality,
                    format_name=format_name,
                    output_path=output_path,
                    **kwargs,
                )
                with lock:
                    results.append(result)
                return result

            with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                futures_list = [executor.submit(download_one, url) for url in urls]
                concurrent.futures.wait(futures_list)

        else:
            for url in urls:
                result = self.download(
                    url=url,
                    quality=quality,
                    format_name=format_name,
                    output_path=output_path,
                    **kwargs,
                )
                results.append(result)

        return results

    def get_download_progress(self, task_id: str) -> Optional[DownloadProgress]:
        """
        Get progress for a download task

        Args:
            task_id: Task identifier

        Returns:
            DownloadProgress or None
        """
        return self.progress_tracker.get_progress(task_id)

    def get_all_downloads(self) -> Dict[str, DownloadProgress]:
        """
        Get all download progress

        Returns:
            Dictionary of task_id -> DownloadProgress
        """
        return self.progress_tracker.get_all_progress()

    def cancel_download(self, task_id: str) -> bool:
        """
        Cancel a download task

        Args:
            task_id: Task identifier

        Returns:
            True if cancelled, False if not found
        """
        progress = self.progress_tracker.get_progress(task_id)
        if progress and progress.status == DownloadStatus.DOWNLOADING:
            self.progress_tracker.set_cancelled(task_id)
            return True
        return False

    def get_download_history(self) -> List[DownloadResult]:
        """
        Get download history

        Returns:
            List of DownloadResult objects
        """
        return self.download_history.copy()

    def clear_history(self):
        """Clear download history"""
        self.download_history.clear()
        self.progress_tracker.clear_all()

    def get_supported_platforms(self) -> List[str]:
        """Get list of supported platforms"""
        return ["youtube", "facebook", "instagram"]

    def is_supported(self, url: str) -> bool:
        """
        Check if URL is supported

        Args:
            url: Video URL

            Returns:
                True if supported, False otherwise
        """
        return detect_platform(url) != Platform.UNKNOWN

    def get_quality_options(self) -> List[Dict]:
        """Get available quality options"""
        return self.quality_manager.get_available_qualities_info()

    def configure(
        self,
        default_quality: Optional[str] = None,
        default_format: Optional[str] = None,
        output_dir: Optional[str] = None,
    ):
        """
        Configure downloader settings

        Args:
            default_quality: Default quality preset
            default_format: Default output format
            output_dir: Default output directory
        """
        if default_quality:
            self.default_quality = default_quality
        if default_format:
            self.default_format = default_format
        if output_dir:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)
