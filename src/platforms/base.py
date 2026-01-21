"""Base platform handler"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import yt_dlp

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.downloader import DownloadResult, VideoInfo


class BasePlatformHandler(ABC):
    """Base class for platform-specific handlers"""
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Name of the platform"""
        pass
    
    @property
    @abstractmethod
    def supported_domains(self) -> List[str]:
        """List of supported domain patterns"""
        pass
    
    @property
    @abstractmethod
    def recommended_quality(self) -> str:
        """Recommended quality for this platform"""
        pass
    
    def is_supported(self, url: str) -> bool:
        """Check if URL is supported by this handler"""
        url_lower = url.lower()
        return any(domain in url_lower for domain in self.supported_domains)
    
    def _extract_info(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Extract video information from URL
        
        Args:
            url: Video URL
            **kwargs: Additional options
            
        Returns:
            Video info dictionary
        """
        options = {
            'quiet': True,
            'no_warnings': True,
            'dump_single_json': True,
        }
        options.update(kwargs)
        
        with yt_dlp.YoutubeDL(options) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                return info
            except Exception as e:
                raise Exception(f"Failed to extract info from {url}: {str(e)}")
    
    def _download(self, url: str, options: Dict) -> DownloadResult:
        """
        Download video with given options
        
        Args:
            url: Video URL
            options: yt-dlp options
            
        Returns:
            DownloadResult object
        """
        with yt_dlp.YoutubeDL(options) as ydl:
            try:
                ydl.download([url])
                return DownloadResult(
                    success=True,
                    url=url,
                    platform=self.platform_name,
                    message="Download completed",
                )
            except Exception as e:
                return DownloadResult(
                    success=False,
                    url=url,
                    platform=self.platform_name,
                    error=str(e),
                    message=f"Download failed: {str(e)}",
                )
    
    @abstractmethod
    def get_video_info(self, url: str) -> VideoInfo:
        """Get video metadata"""
        pass
    
    def get_download_options(self, quality: str = 'best') -> Dict:
        """
        Get download options for the platform
        
        Args:
            quality: Quality preset
            
        Returns:
            Dictionary of yt-dlp options
        """
        return {
            'format': 'best',
            'quiet': False,
            'no_warnings': True,
            'progress': True,
        }
    
    def download(
        self,
        url: str,
        quality: str = 'best',
        output_path: str = './downloads',
        **kwargs
    ) -> DownloadResult:
        """
        Download a video from URL
        
        Args:
            url: Video URL
            quality: Quality preset
            output_path: Output directory
            **kwargs: Additional options
            
        Returns:
            DownloadResult object
        """
        options = self.get_download_options(quality)
        options['outtmpl'] = f'{output_path}/%(title)s.%(ext)s'
        
        # Add progress hook if provided
        if 'progress_hook' in kwargs:
            options['progress_hooks'] = [kwargs['progress_hook']]
        
        return self._download(url, options)
    
    def get_available_qualities(self) -> List[str]:
        """Get available quality options for this platform"""
        return ['best', '1080p', '720p', '480p', '360p', 'audio', 'audio_mp3']
