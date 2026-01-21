"""Social Media Downloader - Multi-platform video downloader"""

__version__ = "1.0.0"
__author__ = "Social Media Downloader Team"

from .core.downloader import SocialMediaDownloader
from .core.url_detector import detect_platform, Platform

__all__ = ["SocialMediaDownloader", "detect_platform", "Platform"]
