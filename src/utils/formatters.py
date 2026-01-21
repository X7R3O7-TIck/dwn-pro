"""Response formatting utilities"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import json


def format_bytes(size_bytes: int) -> str:
    """Format bytes to human readable size"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"


def format_duration(seconds: Optional[int]) -> str:
    """Format duration in seconds to readable format"""
    if seconds is None:
        return "N/A"
    
    if seconds < 60:
        return f"{seconds}s"
    
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    
    if minutes < 60:
        return f"{minutes}m {remaining_seconds}s"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    return f"{hours}h {remaining_minutes}m"


def format_speed(bytes_per_second: Optional[float]) -> str:
    """Format download speed"""
    if bytes_per_second is None:
        return "N/A"
    return format_bytes(bytes_per_second) + "/s"


def format_time_remaining(seconds: Optional[int]) -> str:
    """Format remaining time"""
    if seconds is None:
        return "N/A"
    return str(timedelta(seconds=int(seconds)))


def format_timestamp(dt: datetime) -> str:
    """Format datetime to string"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format percentage"""
    return f"{value:.{decimals}f}%"


def format_json(data: Dict[str, Any], indent: int = 2) -> str:
    """Format data as JSON"""
    return json.dumps(data, indent=indent, default=str)


def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def colorize_status(success: bool) -> str:
    """Colorize status (for CLI output)"""
    if success:
        return "✓"  # Green checkmark
    else:
        return "✗"  # Red X


def format_table_row(columns: List[str], widths: List[int]) -> str:
    """Format a table row with fixed widths"""
    row = []
    for col, width in zip(columns, widths):
        row.append(col[:width].ljust(width))
    return " | ".join(row)


def format_download_result(result: Dict[str, Any]) -> str:
    """Format a download result for display"""
    lines = [
        f"Status: {'✓ Success' if result.get('success') else '✗ Failed'}",
        f"Platform: {result.get('platform', 'N/A')}",
        f"Title: {result.get('title', 'N/A')}",
        f"File: {result.get('file_path', 'N/A')}",
    ]
    
    if result.get('file_size'):
        lines.append(f"Size: {format_bytes(result['file_size'])}")
    
    if result.get('error'):
        lines.append(f"Error: {result['error']}")
    
    return "\n".join(lines)


def format_progress_bar(
    current: float,
    total: float,
    width: int = 30,
    fill_char: str = "█",
    empty_char: str = "░"
) -> str:
    """Create a progress bar string"""
    if total == 0:
        percent = 0
    else:
        percent = (current / total) * 100
    
    filled = int(width * current / total)
    bar = fill_char * filled + empty_char * (width - filled)
    
    return f"[{bar}] {percent:.1f}%"
