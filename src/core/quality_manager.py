"""Quality management module"""

from typing import Dict, List, Optional, Union
from dataclasses import dataclass


@dataclass
class QualityOption:
    """Represents a quality option"""
    name: str
    format_string: str
    description: str
    max_height: Optional[int] = None
    is_audio_only: bool = False


# Quality presets for yt-dlp
QUALITY_PRESETS: Dict[str, QualityOption] = {
    'best': QualityOption(
        name='best',
        format_string='bestvideo+bestaudio/best',
        description='Best available quality (video + audio)',
        max_height=None,
    ),
    'worst': QualityOption(
        name='worst',
        format_string='worstvideo+worstaudio/worst',
        description='Worst available quality',
        max_height=None,
    ),
    '4k': QualityOption(
        name='4k',
        format_string='bestvideo[height<=2160]+bestaudio/best[height<=2160]',
        description='Maximum 4K (2160p)',
        max_height=2160,
    ),
    '1080p': QualityOption(
        name='1080p',
        format_string='bestvideo[height<=1080]+bestaudio/best[height<=1080]',
        description='Full HD (1080p)',
        max_height=1080,
    ),
    '720p': QualityOption(
        name='720p',
        format_string='bestvideo[height<=720]+bestaudio/best[height<=720]',
        description='HD (720p)',
        max_height=720,
    ),
    '480p': QualityOption(
        name='480p',
        format_string='bestvideo[height<=480]+bestaudio/best[height<=480]',
        description='SD (480p)',
        max_height=480,
    ),
    '360p': QualityOption(
        name='360p',
        format_string='bestvideo[height<=360]+bestaudio/best[height<=360]',
        description='Low quality (360p)',
        max_height=360,
    ),
    'audio': QualityOption(
        name='audio',
        format_string='bestaudio/best',
        description='Best audio quality only',
        max_height=None,
        is_audio_only=True,
    ),
    'audio_mp3': QualityOption(
        name='audio_mp3',
        format_string='-x --audio-format mp3',
        description='Extract audio as MP3',
        max_height=None,
        is_audio_only=True,
    ),
    'audio_m4a': QualityOption(
        name='audio_m4a',
        format_string='-x --audio-format m4a',
        description='Extract audio as M4A',
        max_height=None,
        is_audio_only=True,
    ),
}


# Format options
AUDIO_FORMATS = ['mp3', 'm4a', 'opus', 'aac', 'flac', 'wav']
VIDEO_FORMATS = ['mp4', 'mkv', 'webm', 'avi']


class QualityManager:
    """Manages quality options and format selection"""
    
    def __init__(self):
        self.available_qualities = QUALITY_PRESETS
    
    def get_quality_option(self, quality: str) -> Optional[QualityOption]:
        """
        Get quality option by name
        
        Args:
            quality: Quality name (e.g., '720p', 'best')
            
        Returns:
            QualityOption or None
        """
        return self.available_qualities.get(quality.lower())
    
    def get_quality_format_string(self, quality: str) -> str:
        """
        Get yt-dlp format string for quality
        
        Args:
            quality: Quality name
            
        Returns:
            Format string for yt-dlp
        """
        option = self.get_quality_option(quality)
        if option:
            return option.format_string
        return self.available_qualities['best'].format_string
    
    def get_available_qualities(self) -> List[str]:
        """Get list of available quality names"""
        return list(self.available_qualities.keys())
    
    def get_available_qualities_info(self) -> List[Dict]:
        """Get detailed info about available qualities"""
        return [
            {
                'name': q.name,
                'description': q.description,
                'max_height': q.max_height,
                'is_audio_only': q.is_audio_only,
            }
            for q in self.available_qualities.values()
        ]
    
    def get_audio_formats(self) -> List[str]:
        """Get available audio formats"""
        return AUDIO_FORMATS.copy()
    
    def get_video_formats(self) -> List[str]:
        """Get available video formats"""
        return VIDEO_FORMATS.copy()
    
    def is_audio_only_quality(self, quality: str) -> bool:
        """Check if quality is audio only"""
        option = self.get_quality_option(quality)
        return option.is_audio_only if option else False
    
    def get_default_quality(self) -> str:
        """Get default quality preset"""
        return 'best'
    
    def validate_quality(self, quality: str) -> bool:
        """Validate if quality is supported"""
        return quality.lower() in self.available_qualities
    
    def get_quality_for_height(self, max_height: int) -> str:
        """
        Get best quality for given height
        
        Args:
            max_height: Maximum video height
            
        Returns:
            Quality name
        """
        suitable = []
        for name, option in self.available_qualities.items():
            if option.max_height and option.max_height <= max_height:
                suitable.append((option.max_height, name))
        
        if suitable:
            # Return highest quality that fits
            suitable.sort(reverse=True)
            return suitable[0][1]
        
        return 'best'
    
    def build_download_options(
        self,
        quality: str = 'best',
        format_name: str = 'mp4',
        output_template: str = '%(title)s.%(ext)s',
        **kwargs
    ) -> Dict:
        """
        Build yt-dlp download options
        
        Args:
            quality: Quality preset name
            format_name: Output format (mp4, mkv, etc.)
            output_template: Output filename template
            **kwargs: Additional options
            
        Returns:
            Dictionary of yt-dlp options
        """
        quality_option = self.get_quality_option(quality)
        
        options = {
            'format': quality_option.format_string if quality_option else 'best',
            'outtmpl': output_template,
            'quiet': kwargs.get('quiet', False),
            'no_warnings': kwargs.get('no_warnings', True),
            'progress': kwargs.get('progress', True),
        }
        
        # Add format-specific options
        if self.is_audio_only_quality(quality):
            audio_format = format_name if format_name in AUDIO_FORMATS else 'mp3'
            audio_quality = kwargs.get('audio_quality', '192')
            options['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': audio_format,
                'preferredquality': str(audio_quality),
            }]
        else:
            if format_name == 'mp4':
                options['postprocessors'] = [{
                    'key': 'FFmpegEmbedSubtitle',
                }]
                # Add remux option if specified
                if kwargs.get('remux_video'):
                    options['postprocessor_args'] = ['-movflags', '+faststart']
        
        # Add any additional options
        options.update(kwargs)
        
        return options
    
    def get_recommended_quality(self, platform: str, preferred_height: Optional[int] = None) -> str:
        """
        Get recommended quality based on platform and preference
        
        Args:
            platform: Platform name
            preferred_height: Preferred maximum height
            
        Returns:
            Quality name
        """
        if preferred_height:
            return self.get_quality_for_height(preferred_height)
        
        # Platform-specific defaults
        platform_defaults = {
            'youtube': 'best',
            'facebook': '720p',
            'instagram': '720p',
        }
        
        return platform_defaults.get(platform, 'best')
