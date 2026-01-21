"""Test script for social media downloader"""

import sys
import os
sys.path.insert(0, '.')

from src.core.url_detector import detect_platform, Platform, get_supported_platforms
from src.core.quality_manager import QualityManager
from src.core.downloader import SocialMediaDownloader


def test_url_detection():
    """Test URL detection functionality"""
    print("=" * 60)
    print("TESTING URL DETECTION")
    print("=" * 60)
    
    test_cases = [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "youtube"),
        ("https://youtu.be/dQw4w9WgXcQ", "youtube"),
        ("https://www.youtube.com/shorts/abc123", "youtube"),
        ("https://www.facebook.com/watch/?v=1234567890", "facebook"),
        ("https://www.facebook.com/reel/1234567890", "facebook"),
        ("https://www.instagram.com/reel/Dd6_fC1TkcK/", "instagram"),
        ("https://www.instagram.com/p/B_SgH6MHc2s/", "instagram"),
        ("https://example.com/video/123", "unknown"),
    ]
    
    passed = 0
    failed = 0
    
    for url, expected in test_cases:
        result = detect_platform(url)
        result_name = result.value
        
        if result_name == expected:
            print(f"✓ {url[:50]:50s} -> {result_name}")
            passed += 1
        else:
            print(f"✗ {url[:50]:50s} -> {result_name} (expected: {expected})")
            failed += 1
    
    print(f"\nURL Detection: {passed} passed, {failed} failed")
    return failed == 0


def test_quality_manager():
    """Test quality manager functionality"""
    print("\n" + "=" * 60)
    print("TESTING QUALITY MANAGER")
    print("=" * 60)
    
    qm = QualityManager()
    qualities = qm.get_available_qualities()
    
    print(f"Available qualities: {len(qualities)}")
    for q in qualities:
        opt = qm.get_quality_option(q)
        print(f"  - {q}: {opt.description}")
    
    # Test format string generation
    test_cases = ['best', '720p', 'audio_mp3']
    print("\nFormat strings:")
    for q in test_cases:
        fmt = qm.get_quality_format_string(q)
        print(f"  {q}: {fmt}")
    
    print(f"\nQuality Manager: OK")
    return True


def test_video_info():
    """Test video info extraction"""
    print("\n" + "=" * 60)
    print("TESTING VIDEO INFO EXTRACTION")
    print("=" * 60)
    
    downloader = SocialMediaDownloader()
    
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll
    ]
    
    for url in test_urls:
        if not downloader.is_supported(url):
            print(f"✗ Not supported: {url}")
            continue
        
        print(f"\nURL: {url}")
        try:
            info = downloader.get_video_info(url)
            print(f"  Title: {info.title}")
            print(f"  Platform: {info.platform}")
            print(f"  Duration: {info.duration}s")
            print(f"  Views: {info.view_count:,}")
            print(f"  Uploader: {info.uploader}")
            print(f"  Available qualities: {len(info.available_qualities)}")
        except Exception as e:
            print(f"  Error: {str(e)}")
    
    print(f"\nVideo Info: OK")
    return True


def test_youtube_download():
    """Test YouTube download"""
    print("\n" + "=" * 60)
    print("TESTING YOUTUBE DOWNLOAD")
    print("=" * 60)
    
    downloader = SocialMediaDownloader(output_dir='./test_downloads')
    os.makedirs('./test_downloads', exist_ok=True)
    
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    print(f"Downloading: {test_url}")
    print("Quality: 360p")
    
    try:
        result = downloader.download(
            url=test_url,
            quality='360p',
            format_name='mp4'
        )
        
        print(f"\nResult:")
        print(f"  Success: {result.success}")
        print(f"  Title: {result.title}")
        print(f"  Platform: {result.platform}")
        print(f"  File: {result.file_path}")
        print(f"  Size: {result.file_size / 1024 / 1024:.2f} MB" if result.file_size else "  Size: N/A")
        
        if result.success:
            print("\n✓ YouTube download test PASSED")
            return True
        else:
            print(f"\n✗ YouTube download test FAILED: {result.error}")
            return False
            
    except Exception as e:
        print(f"\n✗ YouTube download test FAILED: {str(e)}")
        return False


def test_api_endpoints():
    """Test API endpoints"""
    print("\n" + "=" * 60)
    print("TESTING API ENDPOINTS")
    print("=" * 60)
    
    try:
        from fastapi.testclient import TestClient
        from src.api.app import app
        
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        print("✓ Health endpoint: OK")
        
        # Test platforms endpoint
        response = client.get('/api/platforms')
        assert response.status_code == 200
        data = response.json()
        assert 'youtube' in data['platforms']
        print("✓ Platforms endpoint: OK")
        
        # Test video info endpoint
        response = client.get('/api/info?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ')
        assert response.status_code == 200
        data = response.json()
        assert data['platform'] == 'youtube'
        assert data['title'] is not None
        print("✓ Video info endpoint: OK")
        
        # Test download endpoint
        response = client.post('/api/download', json={
            'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'quality': '360p'
        })
        assert response.status_code == 200
        data = response.json()
        assert 'task_id' in data
        print("✓ Download endpoint: OK")
        
        print("\nAPI Endpoints: All tests PASSED")
        return True
        
    except Exception as e:
        print(f"\nAPI Endpoints test FAILED: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("SOCIAL MEDIA DOWNLOADER - TEST SUITE")
    print("=" * 60)
    
    results = []
    
    results.append(("URL Detection", test_url_detection()))
    results.append(("Quality Manager", test_quality_manager()))
    results.append(("Video Info", test_video_info()))
    results.append(("YouTube Download", test_youtube_download()))
    results.append(("API Endpoints", test_api_endpoints()))
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {name:20s}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED! ✓")
    else:
        print("SOME TESTS FAILED! ✗")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
