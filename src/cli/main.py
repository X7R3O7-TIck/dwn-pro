"""CLI commands for social media downloader"""

import click
from typing import List
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.downloader import SocialMediaDownloader
from core.url_detector import detect_platform, get_supported_platforms


@click.group()
@click.version_option(version="1.0.0")
@click.pass_context
def main(ctx):
    """Social Media Downloader - Download videos from YouTube, Facebook, and Instagram"""
    ctx.ensure_object(dict)
    ctx.obj['downloader'] = SocialMediaDownloader()


@main.command()
@click.argument('url', type=str)
@click.option('--quality', '-q', type=str, default='best', help='Quality preset (best, 1080p, 720p, 480p, 360p, audio)')
@click.option('--format', '-f', type=str, default='mp4', help='Output format (mp4, mkv)')
@click.option('--output', '-o', type=str, default=None, help='Output directory')
@click.pass_context
def download(ctx, url: str, quality: str, format: str, output: str):
    """Download a video from URL"""
    downloader = ctx.obj['downloader']
    
    if not downloader.is_supported(url):
        platform = detect_platform(url).value if detect_platform(url) else 'unknown'
        supported = get_supported_platforms()
        click.echo(f"Error: Unsupported platform '{platform}'")
        click.echo(f"Supported platforms: {', '.join(supported)}")
        return
    
    click.echo(f"Starting download for: {url}")
    click.echo(f"Quality: {quality}")
    click.echo(f"Format: {format}")
    click.echo("-" * 50)
    
    try:
        result = downloader.download(
            url=url,
            quality=quality,
            format_name=format,
            output_path=output,
        )
        
        if result.success:
            click.echo(f"✓ Download completed!")
            click.echo(f"  Title: {result.title}")
            click.echo(f"  Platform: {result.platform}")
            click.echo(f"  File: {result.file_path}")
            if result.file_size:
                click.echo(f"  Size: {result.file_size / 1024 / 1024:.2f} MB")
        else:
            click.echo(f"✗ Download failed: {result.error}")
            
    except Exception as e:
        click.echo(f"Error: {str(e)}")


@main.command()
@click.argument('urls', type=str, nargs=-1)
@click.option('--file', '-F', type=click.File('r'), help='File containing URLs (one per line)')
@click.option('--quality', '-q', type=str, default='best', help='Quality preset')
@click.option('--format', '-f', type=str, default='mp4', help='Output format')
@click.option('--output', '-o', type=str, default=None, help='Output directory')
@click.option('--concurrent/--no-concurrent', default=True, help='Download concurrently')
@click.pass_context
def download_batch(ctx, urls: tuple, file, quality: str, format: str, output: str, concurrent: bool):
    """Download multiple videos"""
    downloader = ctx.obj['downloader']
    
    # Collect URLs
    url_list: List[str] = list(urls)
    if file:
        url_list.extend([line.strip() for line in file if line.strip()])
    
    if not url_list:
        click.echo("Error: No URLs provided")
        return
    
    click.echo(f"Starting batch download of {len(url_list)} videos")
    click.echo(f"Quality: {quality}")
    click.echo(f"Concurrent: {'Yes' if concurrent else 'No'}")
    click.echo("-" * 50)
    
    try:
        results = downloader.download_batch(
            urls=url_list,
            quality=quality,
            format_name=format,
            output_path=output,
            concurrent=concurrent,
        )
        
        success_count = sum(1 for r in results if r.success)
        failed_count = len(results) - success_count
        
        click.echo(f"\nBatch complete!")
        click.echo(f"  Successful: {success_count}")
        click.echo(f"  Failed: {failed_count}")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}")


@main.command()
@click.argument('url', type=str)
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
@click.pass_context
def info(ctx, url: str, as_json: bool):
    """Get video information"""
    downloader = ctx.obj['downloader']
    
    if not downloader.is_supported(url):
        click.echo(f"Error: Unsupported URL")
        return
    
    try:
        info = downloader.get_video_info(url)
        
        if as_json:
            import json
            click.echo(json.dumps(info.to_dict(), indent=2))
        else:
            click.echo(f"Title: {info.title or 'N/A'}")
            click.echo(f"Platform: {info.platform}")
            click.echo(f"Duration: {info.duration or 'N/A'} seconds")
            click.echo(f"Uploader: {info.uploader or 'N/A'}")
            click.echo(f"Views: {info.view_count or 'N/A'}")
            click.echo(f"Available qualities: {', '.join(info.available_qualities)}")
            
    except Exception as e:
        click.echo(f"Error: {str(e)}")


@main.command()
@click.pass_context
def qualities(ctx):
    """List available quality options"""
    downloader = ctx.obj['downloader']
    options = downloader.get_quality_options()
    
    click.echo("Available quality options:")
    click.echo("-" * 50)
    for opt in options:
        click.echo(f"  {opt['name']:12} - {opt['description']}")


@main.command()
@click.pass_context
def platforms(ctx):
    """List supported platforms"""
    downloader = ctx.obj['downloader']
    platforms = downloader.get_supported_platforms()
    
    click.echo("Supported platforms:")
    for p in platforms:
        click.echo(f"  - {p}")


@main.command()
@click.pass_context
def history(ctx):
    """Show download history"""
    downloader = ctx.obj['downloader']
    history = downloader.get_download_history()
    
    if not history:
        click.echo("No download history")
        return
    
    click.echo("Download history:")
    click.echo("-" * 100)
    
    for item in history:
        status = "✓" if item.success else "✗"
        platform = item.platform[:3].upper()
        title = item.title[:30] if item.title else "Unknown"
        file_path = item.file_path if item.file_path else "N/A"
        
        click.echo(f"{status} [{platform}] {title}")
        click.echo(f"    URL: {item.url}")
        click.echo(f"    File: {file_path}")
        click.echo(f"    Time: {item.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo("")


@main.command()
@click.pass_context
def clear_history(ctx):
    """Clear download history"""
    downloader = ctx.obj['downloader']
    downloader.clear_history()
    click.echo("History cleared")


@main.command()
@click.option('--host', '-h', type=str, default='0.0.0.0', help='Host to bind')
@click.option('--port', '-p', type=int, default=8000, help='Port to bind')
@click.pass_context
def serve(ctx, host: str, port: int):
    """Start the API server"""
    import uvicorn
    from api.app import app
    
    click.echo(f"Starting API server on {host}:{port}")
    click.echo("Press Ctrl+C to stop")
    click.echo("")
    
    uvicorn.run(app, host=host, port=port)


@main.command()
@click.pass_context
def test(ctx):
    """Test the downloader with sample URLs"""
    downloader = ctx.obj['downloader']
    
    test_urls = {
        'youtube': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    }
    
    click.echo("Testing downloader functionality...")
    click.echo("-" * 50)
    
    for platform, url in test_urls.items():
        click.echo(f"\nTesting {platform}: {url}")
        
        if not downloader.is_supported(url):
            click.echo(f"  ✗ Platform not supported")
            continue
        
        try:
            info = downloader.get_video_info(url)
            if info.title:
                click.echo(f"  ✓ Got info: {info.title}")
            else:
                click.echo(f"  ✗ Could not get video info")
        except Exception as e:
            click.echo(f"  ✗ Error: {str(e)}")
    
    click.echo("\nTest complete!")
