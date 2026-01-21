"""URL validation utilities"""

import re
from typing import Optional, Tuple
from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    """Check if string is a valid URL"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def is_http_url(url: str) -> bool:
    """Check if URL is HTTP/HTTPS"""
    if not is_valid_url(url):
        return False
    parsed = urlparse(url)
    return parsed.scheme in ('http', 'https')


def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    if not is_valid_url(url):
        return ""
    parsed = urlparse(url)
    return parsed.netloc


def normalize_url(url: str) -> str:
    """Normalize URL by adding scheme if missing"""
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url


def is_youtube_url(url: str) -> bool:
    """Check if URL is YouTube"""
    youtube_patterns = [
        r'youtube\.com/watch',
        r'youtu\.be/',
        r'youtube\.com/shorts',
        r'youtube\.com/playlist',
        r'youtube-nocookie\.com',
    ]
    url = url.lower()
    return any(re.search(pattern, url) for pattern in youtube_patterns)


def is_facebook_url(url: str) -> bool:
    """Check if URL is Facebook"""
    fb_patterns = [
        r'facebook\.com/.*videos?',
        r'facebook\.com/watch/.*v',
        r'facebook\.com/reel/',
        r'fb\.watch/',
    ]
    url = url.lower()
    return any(re.search(pattern, url) for pattern in fb_patterns)


def is_instagram_url(url: str) -> bool:
    """Check if URL is Instagram"""
    ig_patterns = [
        r'instagram\.com/reel/',
        r'instagram\.com/p/',
        r'instagr\.am/p/',
        r'instagram\.com/tv/',
    ]
    url = url.lower()
    return any(re.search(pattern, url) for pattern in ig_patterns)


def extract_video_id_from_youtube(url: str) -> Optional[str]:
    """Extract video ID from YouTube URL"""
    patterns = [
        r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        r'youtu\.be/([a-zA-Z0-9_-]+)',
        r'youtube\.com/shorts/([a-zA-Z0-9_-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def extract_video_id_from_facebook(url: str) -> Optional[str]:
    """Extract video ID from Facebook URL"""
    patterns = [
        r'facebook\.com/.*/videos?/([a-zA-Z0-9_-]+)',
        r'facebook\.com/watch/\?v=([a-zA-Z0-9]+)',
        r'facebook\.com/reel/([a-zA-Z0-9_-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def extract_video_id_from_instagram(url: str) -> Optional[str]:
    """Extract post/reel ID from Instagram URL"""
    patterns = [
        r'instagram\.com/(?:reel|p)/([a-zA-Z0-9_-]+)',
        r'instagram\.com/tv/([a-zA-Z0-9_-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def parse_batch_urls(url_string: str) -> Tuple[str, list]:
    """
    Parse a string containing URLs
    
    Supports:
    - Single URL
    - Multiple URLs separated by newlines
    - URLs from file (prefixed with @)
    
    Returns:
        Tuple of (platform, list of URLs)
    """
    urls = []
    
    # Handle file input
    if url_string.startswith('@'):
        filename = url_string[1:]
        try:
            with open(filename, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
        except Exception:
            return "error", []
    else:
        # Handle multiple URLs
        urls = [u.strip() for u in url_string.split('\n') if u.strip()]
        if len(urls) == 1:
            urls = urls[0].split(',')
            urls = [u.strip() for u in urls if u.strip()]
    
    # Detect common platform
    platform = "mixed"
    if urls:
        first_url = urls[0].lower()
        if is_youtube_url(first_url):
            platform = "youtube"
        elif is_facebook_url(first_url):
            platform = "facebook"
        elif is_instagram_url(first_url):
            platform = "instagram"
    
    return platform, urls
