"""YouTube-specific download handler"""

from typing import Dict, List, Optional
from .base import BasePlatformHandler, DownloadResult, VideoInfo


class YouTubeHandler(BasePlatformHandler):
    """Handler for YouTube video downloads"""
    
    @property
    def platform_name(self) -> str:
        return "youtube"
    
    @property
    def supported_domains(self) -> List[str]:
        return [
            'youtube.com',
            'youtu.be',
            'youtube-nocookie.com',
        ]
    
    @property
    def recommended_quality(self) -> str:
        return "best"
    
    def get_video_info(self, url: str) -> VideoInfo:
        """Get YouTube video information"""
        info = self._extract_info(url)
        
        return VideoInfo(
            url=url,
            platform=self.platform_name,
            title=info.get('title'),
            description=info.get('description'),
            thumbnail=info.get('thumbnail'),
            duration=info.get('duration'),
            uploader=info.get('uploader'),
            upload_date=info.get('upload_date'),
            view_count=info.get('view_count'),
            like_count=info.get('like_count'),
            available_formats=self._get_formats_info(info),
            available_qualities=['4k', '1080p', '720p', '480p', '360p', 'audio', 'audio_mp3'],
            is_live=info.get('is_live', False),
        )
    
    def _get_formats_info(self, info: Dict) -> List[Dict]:
        """Extract format information from video info"""
        formats = []
        if 'formats' in info:
            for f in info['formats'][:20]:
                formats.append({
                    'format_id': f.get('format_id'),
                    'ext': f.get('ext'),
                    'resolution': f.get('resolution'),
                    'format_note': f.get('format_note'),
                    'filesize': f.get('filesize'),
                    'vcodec': f.get('vcodec'),
                    'acodec': f.get('acodec'),
                })
        return formats
    
    def get_download_options(self, quality: str = 'best') -> Dict:
        """Get YouTube-specific download options"""
        base_options = super().get_download_options(quality)
        
        # YouTube-specific options
        youtube_options = {
            'format': self._get_quality_format(quality),
            'writethumbnail': False,
            'writeannotations': False,
        }
        
        base_options.update(youtube_options)
        return base_options
    
    def _get_quality_format(self, quality: str) -> str:
        """Map quality preset to YouTube format string"""
        quality_maps = {
            'best': 'bestvideo+bestaudio/best',
            '4k': 'bestvideo[height<=2160]+bestaudio/best[height<=2160]',
            '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
            '360p': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
            'audio': 'bestaudio/best',
            'audio_mp3': '-x --audio-format mp3',
        }
        return quality_maps.get(quality, quality_maps['best'])
    
    def handle_special_content(self, url: str) -> Optional[DownloadResult]:
        """Handle YouTube-specific content types"""
        if '/shorts/' in url:
            # Handle YouTube Shorts
            return self.download(url, quality=self.recommended_quality)
        elif '/playlist?' in url or '&list=' in url:
            # Handle playlists - return info only
            return None
        elif '/live/' in url:
            # Handle live streams
            return self.download(url, quality=self.recommended_quality)
        
        return None
