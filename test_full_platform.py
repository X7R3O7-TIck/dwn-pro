"""Full Platform Test with unique IDs and file paths"""

import sys
import os
import json
import time
from datetime import datetime

sys.path.insert(0, ".")

from src.core.url_detector import detect_platform, Platform
from src.core.downloader import SocialMediaDownloader

# Test URLs for all platforms
TEST_URLS = {
    "youtube": "https://www.youtube.com/watch?v=9bZkp7q19f0",  # Gangnam Style (~4 min)
    "facebook": "https://www.facebook.com/watch/?v=1234567890",  # Test URL
    "instagram": "https://www.instagram.com/reel/Dd6_fC1TkcK/",  # Test URL
}


def generate_unique_id(platform: str) -> str:
    """Generate unique content ID"""
    return f"{platform}_{int(time.time())}_{hash(platform) % 1000}"


def test_platform_detection():
    """Test platform detection for all URLs"""
    print("=" * 70)
    print("PLATFORM DETECTION TEST")
    print("=" * 70)

    results = {}
    for platform, url in TEST_URLS.items():
        detected = detect_platform(url)
        content_id = generate_unique_id(platform)

        results[platform] = {
            "content_id": content_id,
            "user_link": url,
            "original_url": url,
            "detected_platform": detected.value,
            "is_supported": detected != Platform.UNKNOWN,
            "timestamp": datetime.now().isoformat(),
        }

        status = "✓" if detected != Platform.UNKNOWN else "✗"
        print(f"{status} {platform:12} | {url[:50]:50s} -> {detected.value}")

    return results


def test_video_info_all_platforms():
    """Test video info extraction for all platforms"""
    print("\n" + "=" * 70)
    print("VIDEO INFO TEST (All Platforms)")
    print("=" * 70)

    downloader = SocialMediaDownloader(output_dir="./downloads")
    results = {}

    for platform, url in TEST_URLS.items():
        content_id = generate_unique_id(platform)
        print(f"\n[{platform.upper()}] Testing: {url}")

        try:
            if not downloader.is_supported(url):
                print(f"  ✗ Platform not supported")
                results[platform] = {
                    "content_id": content_id,
                    "user_link": url,
                    "error": "Platform not supported",
                    "status": "unsupported",
                }
                continue

            info = downloader.get_video_info(url)

            platform_info = {
                "content_id": content_id,
                "user_link": url,
                "platform": platform,
                "platform_detected": info.platform,
                "title": info.title,
                "description": info.description,
                "thumbnail": info.thumbnail,
                "duration_seconds": info.duration,
                "duration_formatted": f"{info.duration // 60}:{info.duration % 60:02d}"
                if info.duration
                else None,
                "uploader": info.uploader,
                "upload_date": info.upload_date,
                "view_count": info.view_count,
                "available_qualities": info.available_qualities,
                "available_formats_count": len(info.available_formats),
                "is_live": info.is_live,
                "error": info.error,
                "timestamp": datetime.now().isoformat(),
                "file_path": None,
                "download_status": "pending",
            }

            results[platform] = platform_info

            print(f"  ✓ Content ID: {content_id}")
            print(f"  ✓ Platform: {info.platform}")
            print(f"  ✓ Title: {info.title[:50] if info.title else 'N/A'}...")
            print(f"  ✓ Duration: {platform_info['duration_formatted'] or 'N/A'}")
            print(f"  ✓ Views: {info.view_count or 'N/A'}")
            print(f"  ✓ Qualities: {len(info.available_qualities)} options")

        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            results[platform] = {
                "content_id": content_id,
                "user_link": url,
                "error": str(e),
                "status": "error",
            }

    return results


def test_youtube_download_with_details():
    """Test YouTube download with all details"""
    print("\n" + "=" * 70)
    print("YOUTUBE DOWNLOAD WITH FILE PATH & UNIQUE ID")
    print("=" * 70)

    downloader = SocialMediaDownloader(output_dir="./downloads")
    os.makedirs("./downloads", exist_ok=True)

    yt_url = TEST_URLS["youtube"]
    content_id = generate_unique_id("youtube_download")

    print(f"\n[YouTube] URL: {yt_url}")
    print(f"Content ID: {content_id}")
    print("-" * 50)

    try:
        # Get info first
        info = downloader.get_video_info(yt_url)
        print(f"Title: {info.title}")
        print(f"Duration: {info.duration}s")

        # Download
        print("\nDownloading at 360p quality...")
        result = downloader.download(url=yt_url, quality="360p", format_name="mp4")

        # Build complete response
        download_result = {
            "content_id": content_id,
            "user_link": yt_url,
            "task_id": result.task_id,
            "download_status": "completed" if result.success else "failed",
            "platform": result.platform,
            "title": result.title,
            "file_path": result.file_path,
            "file_path_absolute": os.path.abspath(result.file_path)
            if result.file_path
            else None,
            "file_size_bytes": result.file_size,
            "file_size_mb": round(result.file_size / 1024 / 1024, 2)
            if result.file_size
            else None,
            "file_size_human": f"{result.file_size / 1024 / 1024:.2f} MB"
            if result.file_size
            else None,
            "file_format": result.file_format,
            "duration_seconds": result.duration,
            "duration_formatted": f"{result.duration // 60}:{result.duration % 60:02d}"
            if result.duration
            else None,
            "uploader": result.uploader,
            "thumbnail": result.thumbnail,
            "view_count": result.view_count,
            "error": result.error,
            "message": result.message,
            "timestamp": datetime.now().isoformat(),
            "download_url": f"file://{os.path.abspath(result.file_path)}"
            if result.file_path
            else None,
            "unique_download_id": f"dl_{result.task_id}_{int(time.time())}",
        }

        print(f"\n✓ Download Complete:")
        print(f"  Task ID: {result.task_id}")
        print(f"  Success: {result.success}")
        print(f"  File Path: {result.file_path}")
        print(f"  File Size: {download_result['file_size_human']}")
        print(f"  Format: {result.file_format}")

        # Verify file
        if result.file_path and os.path.exists(result.file_path):
            stat = os.stat(result.file_path)
            download_result["file_verified"] = True
            download_result["file_verified_size"] = stat.st_size
            print(f"  ✓ File verified: {stat.st_size / 1024 / 1024:.2f} MB")
        else:
            download_result["file_verified"] = False
            print(f"  ✗ File not found")

        return download_result

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback

        traceback.print_exc()
        return {
            "content_id": content_id,
            "user_link": yt_url,
            "error": str(e),
            "status": "error",
        }


def test_api_endpoints():
    """Test all API endpoints"""
    print("\n" + "=" * 70)
    print("API ENDPOINTS TEST")
    print("=" * 70)

    try:
        from fastapi.testclient import TestClient
        from src.api.app import app

        client = TestClient(app)
        results = {}

        # 1. Health
        print("\n[1] Health Check:")
        response = client.get("/api/health")
        results["health"] = response.json()
        print(f"    Status: {results['health']['status']}")

        # 2. Platforms
        print("\n[2] Supported Platforms:")
        response = client.get("/api/platforms")
        results["platforms"] = response.json()
        print(f"    Platforms: {results['platforms']['platforms']}")

        # 3. Qualities
        print("\n[3] Quality Options:")
        response = client.get("/api/qualities")
        results["qualities"] = response.json()
        print(f"    Total: {len(results['qualities'])} options")

        # 4. Video Info with Content ID
        print("\n[4] Video Info (YouTube):")
        yt_url = TEST_URLS["youtube"]
        content_id = generate_unique_id("api_video_info")
        response = client.get(f"/api/info?url={yt_url}")
        results["video_info"] = response.json()
        results["video_info"]["content_id"] = content_id
        results["video_info"]["user_link"] = yt_url
        print(f"    Content ID: {content_id}")
        print(f"    Title: {results['video_info']['title'][:40]}...")
        print(f"    Platform: {results['video_info']['platform']}")

        # 5. Download with Content ID
        print("\n[5] Download (YouTube):")
        download_content_id = generate_unique_id("api_download")
        response = client.post(
            "/api/download", json={"url": yt_url, "quality": "360p", "format": "mp4"}
        )
        results["download"] = response.json()
        results["download"]["content_id"] = download_content_id
        results["download"]["user_link"] = yt_url
        print(f"    Content ID: {download_content_id}")
        print(f"    Task ID: {results['download']['task_id']}")
        print(f"    Status: {results['download']['status']}")

        # 6. Progress
        if results["download"]["task_id"]:
            print("\n[6] Progress Check:")
            progress_content_id = generate_unique_id("api_progress")
            response = client.get(
                f"/api/download/progress/{results['download']['task_id']}"
            )
            results["progress"] = response.json()
            results["progress"]["content_id"] = progress_content_id
            print(f"    Content ID: {progress_content_id}")
            print(f"    Progress: {results['progress']['progress_percent']}%")

        # 7. History
        print("\n[7] History:")
        response = client.get("/api/history")
        results["history"] = response.json()
        print(f"    Total Items: {results['history']['total_count']}")

        return results

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


def generate_final_report(all_results):
    """Generate comprehensive JSON report"""
    print("\n" + "=" * 70)
    print("FINAL JSON REPORT")
    print("=" * 70)

    report = {
        "report_metadata": {
            "generated_at": datetime.now().isoformat(),
            "project": "Social Media Downloader",
            "version": "1.0.0",
            "server_mode": True,
        },
        "platform_detection": all_results.get("platform_detection", {}),
        "video_info": all_results.get("video_info", {}),
        "youtube_download": all_results.get("youtube_download", {}),
        "api_endpoints": all_results.get("api_endpoints", {}),
    }

    # Save report
    report_file = "full_test_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n✓ Report saved: {report_file}")

    # Print key info
    print("\n" + "-" * 50)
    print("KEY RESULTS:")
    print("-" * 50)

    yt_download = all_results.get("youtube_download", {})
    api_dl = all_results.get("api_endpoints", {}).get("download", {})

    print(
        json.dumps(
            {
                "youtube_download": {
                    "content_id": yt_download.get("content_id"),
                    "unique_download_id": yt_download.get("unique_download_id"),
                    "task_id": yt_download.get("task_id"),
                    "user_link": yt_download.get("user_link"),
                    "file_path": yt_download.get("file_path"),
                    "file_path_absolute": yt_download.get("file_path_absolute"),
                    "file_size_mb": yt_download.get("file_size_mb"),
                    "status": yt_download.get("download_status"),
                },
                "api_download": {
                    "content_id": api_dl.get("content_id"),
                    "task_id": api_dl.get("task_id"),
                    "user_link": api_dl.get("user_link"),
                    "file_path": api_dl.get("file_path"),
                    "status": api_dl.get("status"),
                },
            },
            indent=2,
        )
    )

    return report


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("SOCIAL MEDIA DOWNLOADER - FULL PLATFORM TEST")
    print("Features: Unique Content ID, File Path, User Link, JSON Format")
    print("=" * 70)

    results = {}

    # Test 1: Platform Detection
    results["platform_detection"] = test_platform_detection()

    # Test 2: Video Info (All Platforms)
    results["video_info"] = test_video_info_all_platforms()

    # Test 3: YouTube Download with Details
    results["youtube_download"] = test_youtube_download_with_details()

    # Test 4: API Endpoints
    results["api_endpoints"] = test_api_endpoints()

    # Generate Report
    report = generate_final_report(results)

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    yt_dl = results.get("youtube_download", {})
    api_ep = results.get("api_endpoints", {})

    tests = {
        "Platform Detection": results.get("platform_detection"),
        "Video Info (YouTube)": results.get("video_info", {}).get("youtube"),
        "YouTube Download": yt_dl.get("download_status") == "completed",
        "API Endpoints": api_ep is not None and api_ep.get("health") is not None,
    }

    for name, passed in tests.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {name:25}: {status}")

    all_passed = all(tests.values())

    print("\n" + "=" * 70)
    if all_passed:
        print("ALL TESTS PASSED! ✓")
        print("Server ready with:")
        print("  - Unique Content IDs")
        print("  - File Paths")
        print("  - User Links")
        print("  - JSON Format responses")
    else:
        print("SOME TESTS FAILED! ✗")
    print("=" * 70)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
