"""Instagram-specific download handler"""

from typing import Dict, List, Optional
from .base import BasePlatformHandler, DownloadResult, VideoInfo


class InstagramHandler(BasePlatformHandler):
    """Handler for Instagram video downloads"""
    
    @property
    def platform_name(self) -> str:
        return "instagram"
    
    @property
    def supported_domains(self) -> List[str]:
        return [
            'instagram.com',
            'instagr.am',
        ]
    
    @property
    def recommended_quality(self) -> str:
        return "720p"
    
    def get_video_info(self, url: str) -> VideoInfo:
        """Get Instagram video information"""
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
        """Get Instagram-specific download options"""
        base_options = super().get_download_options(quality)
        
        # Instagram-specific options
        instagram_options = {
            'format': self._get_quality_format(quality),
            'writethumbnail': False,
            # Instagram may require specific headers
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
            },
        }
        
        base_options.update(instagram_options)
        return base_options
    
    def _get_quality_format(self, quality: str) -> str:
        """Map quality preset to Instagram format string"""
        quality_maps = {
            'best': 'bestvideo+bestaudio/best',
            '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
            '360p': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
            'audio': 'bestaudio/best',
        }
        return quality_maps.get(quality, quality_maps['720p'])
    
    def handle_special_content(self, url: str) -> Optional[DownloadResult]:
        """Handle Instagram-specific content types"""
        if '/reel/' in url:
            return self.download(url, quality=self.recommended_quality)
        elif '/tv/' in url:
            return self.download(url, quality=self.recommended_quality)
        elif '/p/' in url:
            return self.download(url, quality=self.recommended_quality)
        
        return None
