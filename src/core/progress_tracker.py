"""Progress tracking module"""

from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
import json


class DownloadStatus(Enum):
    """Download status states"""
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadProgress:
    """Download progress information"""
    task_id: str
    status: DownloadStatus
    url: str
    platform: str
    title: Optional[str] = None
    progress_percent: float = 0.0
    downloaded_bytes: int = 0
    total_bytes: int = 0
    speed: Optional[str] = None
    eta: Optional[str] = None
    current_file: Optional[str] = None
    message: str = ""
    error: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'task_id': self.task_id,
            'status': self.status.value,
            'url': self.url,
            'platform': self.platform,
            'title': self.title,
            'progress_percent': self.progress_percent,
            'downloaded_bytes': self.downloaded_bytes,
            'total_bytes': self.total_bytes,
            'speed': self.speed,
            'eta': self.eta,
            'current_file': self.current_file,
            'message': self.message,
            'error': self.error,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'timestamp': self.timestamp.isoformat(),
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


class ProgressCallback:
    """Callback handler for progress updates"""
    
    def __init__(self):
        self.callbacks: Dict[str, Callable] = {}
    
    def register(self, event: str, callback: Callable):
        """
        Register a callback for an event
        
        Args:
            event: Event name (progress, complete, error, etc.)
            callback: Callback function
        """
        self.callbacks[event] = callback
    
    def on_progress(self, progress: DownloadProgress):
        """Called during download with progress updates"""
        callback = self.callbacks.get('progress')
        if callback:
            callback(progress)
    
    def on_complete(self, progress: DownloadProgress):
        """Called when download completes"""
        callback = self.callbacks.get('complete')
        if callback:
            callback(progress)
    
    def on_error(self, progress: DownloadProgress):
        """Called when download fails"""
        callback = self.callbacks.get('error')
        if callback:
            callback(progress)
    
    def on_start(self, progress: DownloadProgress):
        """Called when download starts"""
        callback = self.callbacks.get('start')
        if callback:
            callback(progress)


class ProgressTracker:
    """Track download progress for multiple tasks"""
    
    def __init__(self):
        self._tasks: Dict[str, DownloadProgress] = {}
        self._lock = threading.Lock()
        self._callback = ProgressCallback()
    
    def create_task(self, task_id: str, url: str, platform: str) -> DownloadProgress:
        """
        Create a new download task
        
        Args:
            task_id: Unique task identifier
            url: Video URL
            platform: Platform name
            
        Returns:
            DownloadProgress object
        """
        progress = DownloadProgress(
            task_id=task_id,
            status=DownloadStatus.QUEUED,
            url=url,
            platform=platform,
            message="Download queued",
        )
        
        with self._lock:
            self._tasks[task_id] = progress
        
        return progress
    
    def update_progress(
        self,
        task_id: str,
        progress_percent: Optional[float] = None,
        downloaded_bytes: Optional[int] = None,
        total_bytes: Optional[int] = None,
        speed: Optional[str] = None,
        eta: Optional[str] = None,
        current_file: Optional[str] = None,
        message: Optional[str] = None,
        status: Optional[DownloadStatus] = None,
        title: Optional[str] = None,
    ):
        """
        Update task progress
        
        Args:
            task_id: Task identifier
            progress_percent: Download progress percentage
            downloaded_bytes: Bytes downloaded
            total_bytes: Total bytes to download
            speed: Download speed string
            eta: Estimated time remaining
            current_file: Current file being processed
            message: Status message
            status: Download status
            title: Video title
        """
        with self._lock:
            if task_id not in self._tasks:
                return
            
            progress = self._tasks[task_id]
            
            if progress_percent is not None:
                progress.progress_percent = progress_percent
            if downloaded_bytes is not None:
                progress.downloaded_bytes = downloaded_bytes
            if total_bytes is not None:
                progress.total_bytes = total_bytes
            if speed is not None:
                progress.speed = speed
            if eta is not None:
                progress.eta = eta
            if current_file is not None:
                progress.current_file = current_file
            if message is not None:
                progress.message = message
            if status is not None:
                progress.status = status
            if title is not None:
                progress.title = title
            
            progress.timestamp = datetime.now()
            
            # Trigger callback
            self._callback.on_progress(progress)
    
    def set_complete(
        self,
        task_id: str,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        message: str = "Download completed",
        title: Optional[str] = None,
    ):
        """
        Mark task as complete
        
        Args:
            task_id: Task identifier
            file_path: Path to downloaded file
            file_size: File size in bytes
            message: Completion message
            title: Video title
        """
        with self._lock:
            if task_id not in self._tasks:
                return
            
            progress = self._tasks[task_id]
            progress.status = DownloadStatus.COMPLETED
            progress.progress_percent = 100.0
            progress.file_path = file_path
            progress.file_size = file_size
            progress.message = message
            progress.timestamp = datetime.now()
            if title:
                progress.title = title
            
            self._callback.on_complete(progress)
    
    def set_failed(self, task_id: str, error: str, message: str = "Download failed"):
        """
        Mark task as failed
        
        Args:
            task_id: Task identifier
            error: Error description
            message: Error message
        """
        with self._lock:
            if task_id not in self._tasks:
                return
            
            progress = self._tasks[task_id]
            progress.status = DownloadStatus.FAILED
            progress.error = error
            progress.message = message
            progress.timestamp = datetime.now()
            
            self._callback.on_error(progress)
    
    def set_cancelled(self, task_id: str, message: str = "Download cancelled"):
        """
        Mark task as cancelled
        
        Args:
            task_id: Task identifier
            message: Cancellation message
        """
        with self._lock:
            if task_id not in self._tasks:
                return
            
            progress = self._tasks[task_id]
            progress.status = DownloadStatus.CANCELLED
            progress.message = message
            progress.timestamp = datetime.now()
    
    def get_progress(self, task_id: str) -> Optional[DownloadProgress]:
        """
        Get progress for a task
        
        Args:
            task_id: Task identifier
            
        Returns:
            DownloadProgress or None
        """
        with self._lock:
            return self._tasks.get(task_id)
    
    def get_all_progress(self) -> Dict[str, DownloadProgress]:
        """
        Get progress for all tasks
        
        Returns:
            Dictionary of task_id -> DownloadProgress
        """
        with self._lock:
            return self._tasks.copy()
    
    def get_tasks_by_status(self, status: DownloadStatus) -> Dict[str, DownloadProgress]:
        """
        Get tasks filtered by status
        
        Args:
            status: Status to filter by
            
        Returns:
            Dictionary of matching tasks
        """
        with self._lock:
            return {
                tid: prog for tid, prog in self._tasks.items()
                if prog.status == status
            }
    
    def remove_task(self, task_id: str):
        """
        Remove a task from tracking
        
        Args:
            task_id: Task identifier
        """
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
    
    def clear_completed(self):
        """Remove all completed tasks"""
        with self._lock:
            completed_ids = [
                tid for tid, prog in self._tasks.items()
                if prog.status == DownloadStatus.COMPLETED
            ]
            for tid in completed_ids:
                del self._tasks[tid]
    
    def clear_all(self):
        """Clear all tasks"""
        with self._lock:
            self._tasks.clear()
    
    def register_callback(self, event: str, callback: Callable):
        """Register a progress callback"""
        self._callback.register(event, callback)
    
    def create_yt_dlp_hook(self, task_id: str) -> Callable:
        """
        Create a yt-dlp progress hook
        
        Args:
            task_id: Task identifier
            
        Returns:
            Hook function for yt-dlp
        """
        def hook(d):
            status = d.get('status', '')
            
            if status == 'downloading':
                downloaded_bytes = d.get('downloaded_bytes', 0)
                total_bytes = d.get('total_bytes', 0)
                
                # Calculate percentage
                if total_bytes > 0:
                    percent = (downloaded_bytes / total_bytes) * 100
                else:
                    # Try to get percent from d
                    percent = d.get('percent', 0) or 0
                
                speed = d.get('speed', '')
                if speed:
                    speed = f"{speed/1024:.1f} KB/s" if speed < 1024*1024 else f"{speed/1024/1024:.1f} MB/s"
                
                eta = d.get('eta', '')
                if eta:
                    eta = f"{eta}s"
                
                self.update_progress(
                    task_id,
                    progress_percent=percent,
                    downloaded_bytes=downloaded_bytes,
                    total_bytes=total_bytes,
                    speed=speed,
                    eta=eta,
                    status=DownloadStatus.DOWNLOADING,
                )
                
            elif status == 'finished':
                self.set_complete(
                    task_id,
                    file_path=d.get('filename'),
                    file_size=d.get('total_bytes'),
                )
                
            elif status == 'error':
                self.set_failed(task_id, d.get('error', 'Unknown error'))
        
        return hook


# Global progress tracker instance
global_progress_tracker = ProgressTracker()
