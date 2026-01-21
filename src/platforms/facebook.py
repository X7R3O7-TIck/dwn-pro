"""Facebook-specific download handler"""

from typing import Dict, List, Optional
from .base import BasePlatformHandler, DownloadResult, VideoInfo


class FacebookHandler(BasePlatformHandler):
    """Handler for Facebook video downloads"""
    
    @property
    def platform_name(self) -> str:
        return "facebook"
    
    @property
    def supported_domains(self) -> List[str]:
        return [
            'facebook.com',
            'fb.watch',
        ]
    
    @property
    def recommended_quality(self) -> str:
        return "720p"
    
    def get_video_info(self, url: str) -> VideoInfo:
        """Get Facebook video information"""
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
            available_formats=self._get_formats_info(info),
            available_qualities=['720p', '480p', '360p', 'audio'],
            is_live=info.get('is_live', False),
        )
    
    def _get_formats_info(self, info: Dict) -> List[Dict]:
        """Extract format information from video info"""
        formats = []
        if 'formats' in info:
            for f in info['formats'][:15]:
                formats.append({
                    'format_id': f.get('format_id'),
                    'ext': f.get('ext'),
                    'resolution': f.get('resolution'),
                    'format_note': f.get('format_note'),
                    'filesize': f.get('filesize'),
                })
        return formats
    
    def get_download_options(self, quality: str = '720p') -> Dict:
        """Get Facebook-specific download options"""
        base_options = super().get_download_options(quality)
        
        # Facebook-specific options
        facebook_options = {
            'format': self._get_quality_format(quality),
            'writethumbnail': False,
            # Facebook may require specific user agent
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            },
        }
        
        base_options.update(facebook_options)
        return base_options
    
    def _get_quality_format(self, quality: str) -> str:
        """Map quality preset to Facebook format string"""
        quality_maps = {
            'best': 'bestvideo+bestaudio/best',
            '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
            '360p': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
            'audio': 'bestaudio/best',
        }
        return quality_maps.get(quality, quality_maps['720p'])
    
    def handle_special_content(self, url: str) -> Optional[DownloadResult]:
        """Handle Facebook-specific content types"""
        if '/reel/' in url:
            return self.download(url, quality=self.recommended_quality)
        elif '/watch/' in url:
            return self.download(url, quality=self.recommended_quality)
        
        return None
