"""URL and platform detection module"""

from enum import Enum
from typing import Optional
import re


class Platform(Enum):
    """Supported platforms"""
    YOUTUBE = "youtube"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    UNKNOWN = "unknown"


# Platform URL patterns
PLATFORM_PATTERNS = {
    Platform.YOUTUBE: [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(?:https?://)?(?:www\.)?youtu\.be/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/playlist\?list=[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube-nocookie\.com/embed/[\w-]+',
    ],
    Platform.FACEBOOK: [
        r'(?:https?://)?(?:www\.)?facebook\.com/[\w./-]+/videos?/[\w/-]+',
        r'(?:https?://)?(?:www\.)?facebook\.com/watch/\?v=[\w]+',
        r'(?:https?://)?(?:www\.)?facebook\.com/reel/[\w-]+',
        r'(?:https?://)?(?:www\.)?fb\.watch/[\w/-]+',
        r'(?:https?://)?(?:www\.)?facebook\.com/[\w.]+/posts/[\w-]+',
    ],
    Platform.INSTAGRAM: [
        r'(?:https?://)?(?:www\.)?instagram\.com/reel/[\w-]+',
        r'(?:https?://)?(?:www\.)?instagram\.com/p/[\w-]+',
        r'(?:https?://)?(?:www\.)?instagr\.am/p/[\w-]+',
        r'(?:https?://)?(?:www\.)?instagram\.com/tv/[\w-]+',
        r'(?:https?://)?(?:www\.)?instagram\.com/stories/[\w./-]+/[\w-]+',
    ],
}


def detect_platform(url: str) -> Platform:
    """
    Detect platform from URL
    
    Args:
        url: Video URL to detect
        
    Returns:
        Platform enum value
    """
    if not url:
        return Platform.UNKNOWN
    
    # Normalize URL
    url = url.strip().lower()
    
    # Add https:// if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Check each platform
    for platform, patterns in PLATFORM_PATTERNS.items():
        for pattern in patterns:
            if re.match(pattern, url, re.IGNORECASE):
                return platform
    
    return Platform.UNKNOWN


def detect_platform_simple(url: str) -> str:
    """
    Simple platform detection returning string
    
    Args:
        url: Video URL to detect
        
    Returns:
        Platform name string
    """
    platform = detect_platform(url)
    return platform.value


def is_valid_video_url(url: str) -> bool:
    """
    Check if URL is a valid video URL
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid video URL, False otherwise
    """
    return detect_platform(url) != Platform.UNKNOWN


def extract_video_id(url: str, platform: Platform) -> Optional[str]:
    """
    Extract video ID from URL
    
    Args:
        url: Video URL
        platform: Platform enum
        
    Returns:
        Video ID string or None
    """
    if platform == Platform.YOUTUBE:
        # YouTube patterns
        patterns = [
            r'youtube\.com/watch\?v=([\w-]+)',
            r'youtu\.be/([\w-]+)',
            r'youtube\.com/shorts/([\w-]+)',
            r'youtube\.com/embed/([\w-]+)',
        ]
    elif platform == Platform.FACEBOOK:
        # Facebook patterns
        patterns = [
            r'facebook\.com/.*/videos?/([\w-]+)',
            r'facebook\.com/watch/\?v=([\w]+)',
            r'facebook\.com/reel/([\w-]+)',
        ]
    elif platform == Platform.INSTAGRAM:
        # Instagram patterns
        patterns = [
            r'instagram\.com/(?:reel|p)/([\w-]+)',
            r'instagram\.com/tv/([\w-]+)',
        ]
    else:
        return None
    
    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def get_supported_platforms() -> list:
    """Get list of supported platform names"""
    return [p.value for p in Platform if p != Platform.UNKNOWN]
