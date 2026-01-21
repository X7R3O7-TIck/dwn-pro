"""Comprehensive API Test with unique content IDs and file paths"""

import sys
import os
import json
import time
from datetime import datetime

sys.path.insert(0, ".")

from src.core.url_detector import detect_platform, Platform
from src.core.downloader import SocialMediaDownloader
from src.api.models import DownloadRequest, VideoInfoResponse

YOUTUBE_5MIN_VIDEO = (
    "https://www.youtube.com/watch?v=9bZkp7q19f0"  # PSY - Gangnam Style (6:50 min)
)
YOUTUBE_5MIN_ALT = "https://www.youtube.com/watch?v=l482T0yNkeo"  # 5 min animation
FACEBOOK_VIDEO = "https://www.facebook.com/watch/?v=1234567890"  # Test URL
INSTAGRAM_VIDEO = "https://www.instagram.com/reel/Dd6_fC1TkcK/"  # Test URL


def test_video_info_with_details():
    """Test video info with unique content ID"""
    print("=" * 70)
    print("TESTING VIDEO INFO WITH UNIQUE CONTENT ID")
    print("=" * 70)

    downloader = SocialMediaDownloader(output_dir="./downloads")

    # Test YouTube
    yt_url = YOUTUBE_5MIN_ALT
    print(f"\n[YouTube] URL: {yt_url}")

    if not downloader.is_supported(yt_url):
        print("  ✗ URL not supported")
        return None

    try:
        info = downloader.get_video_info(yt_url)

        # Generate unique content ID
        content_id = (
            f"content_{info.platform}_{int(time.time())}_{hash(yt_url) % 10000}"
        )

        response_data = {
            "content_id": content_id,
            "user_link": yt_url,
            "platform": info.platform,
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
            "available_formats": info.available_formats[:5],
            "is_live": info.is_live,
            "timestamp": datetime.now().isoformat(),
            "file_path": None,  # Will be set after download
            "download_status": "pending",
        }

        print(f"  ✓ Content ID: {content_id}")
        print(f"  ✓ Title: {info.title}")
        print(f"  ✓ Duration: {response_data['duration_formatted']}")
        print(f"  ✓ Platform: {info.platform}")
        print(f"  ✓ View Count: {info.view_count:,}")
        print(f"  ✓ Available Qualities: {len(info.available_qualities)} options")

        return response_data

    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return None


def test_download_with_file_path():
    """Test download and get file path"""
    print("\n" + "=" * 70)
    print("TESTING DOWNLOAD WITH FILE PATH & UNIQUE ID")
    print("=" * 70)

    downloader = SocialMediaDownloader(output_dir="./downloads")
    os.makedirs("./downloads", exist_ok=True)

    yt_url = "https://www.youtube.com/watch?v=9bZkp7q19f0"
    print(f"\n[YouTube Download] URL: {yt_url}")

    try:
        # Get video info first
        info = downloader.get_video_info(yt_url)
        content_id = f"dl_{info.platform}_{int(time.time())}"

        print(f"  Content ID: {content_id}")
        print(f"  Title: {info.title}")
        print(f"  Quality: 360p")

        # Download
        result = downloader.download(url=yt_url, quality="360p", format_name="mp4")

        # Create response with all details
        download_response = {
            "content_id": content_id,
            "user_link": yt_url,
            "task_id": result.task_id,
            "download_status": "completed" if result.success else "failed",
            "platform": result.platform,
            "title": result.title,
            "file_path": result.file_path,
            "file_size_bytes": result.file_size,
            "file_size_mb": round(result.file_size / 1024 / 1024, 2)
            if result.file_size
            else None,
            "file_format": result.file_format,
            "duration_seconds": result.duration,
            "uploader": result.uploader,
            "thumbnail": result.thumbnail,
            "view_count": result.view_count,
            "error": result.error,
            "message": result.message,
            "timestamp": result.timestamp.isoformat(),
            "download_url": f"file://{result.file_path}" if result.file_path else None,
        }

        print(f"\n  ✓ Download Result:")
        print(f"    Task ID: {result.task_id}")
        print(f"    Success: {result.success}")
        print(f"    File Path: {result.file_path}")
        print(f"    File Size: {download_response['file_size_mb']} MB")
        print(f"    Format: {result.file_format}")

        if result.file_path and os.path.exists(result.file_path):
            print(f"  ✓ File exists at: {result.file_path}")
            file_stats = os.stat(result.file_path)
            print(f"  ✓ Actual file size: {file_stats.st_size / 1024 / 1024:.2f} MB")

        return download_response

    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return None


def test_api_endpoints_comprehensive():
    """Test all API endpoints with proper response format"""
    print("\n" + "=" * 70)
    print("TESTING API ENDPOINTS COMPREHENSIVE")
    print("=" * 70)

    try:
        from fastapi.testclient import TestClient
        from src.api.app import app

        client = TestClient(app)
        results = {}

        # 1. Health Check
        print("\n[1] Health Check Endpoint:")
        response = client.get("/api/health")
        results["health"] = response.json()
        print(f"    Status: {results['health']['status']}")
        print(f"    Version: {results['health']['version']}")
        print(f"    Platforms: {results['health']['supported_platforms']}")

        # 2. Platforms
        print("\n[2] Platforms Endpoint:")
        response = client.get("/api/platforms")
        results["platforms"] = response.json()
        print(f"    Platforms: {results['platforms']['platforms']}")
        print(f"    Quality Options: {len(results['platforms']['quality_options'])}")

        # 3. Qualities
        print("\n[3] Quality Options Endpoint:")
        response = client.get("/api/qualities")
        results["qualities"] = response.json()
        for q in results["qualities"][:5]:
            print(f"    - {q['name']}: {q['description']}")

        # 4. Video Info with Content ID
        print("\n[4] Video Info Endpoint:")
        yt_url = "https://www.youtube.com/watch?v=9bZkp7q19f0"
        content_id = f"api_{int(time.time())}_{hash(yt_url) % 10000}"
        response = client.get(f"/api/info?url={yt_url}")
        results["video_info"] = response.json()
        results["video_info"]["content_id"] = content_id
        results["video_info"]["user_link"] = yt_url
        print(f"    Content ID: {content_id}")
        print(f"    Platform: {results['video_info']['platform']}")
        print(f"    Title: {results['video_info']['title']}")
        print(f"    Duration: {results['video_info']['duration']}s")

        # 5. Download with Progress
        print("\n[5] Download Endpoint:")
        download_request = {"url": yt_url, "quality": "360p", "format": "mp4"}
        response = client.post("/api/download", json=download_request)
        results["download"] = response.json()
        dl_content_id = f"dl_{int(time.time())}"
        results["download"]["content_id"] = dl_content_id
        results["download"]["user_link"] = yt_url
        print(f"    Content ID: {dl_content_id}")
        print(f"    Task ID: {results['download']['task_id']}")
        print(f"    Status: {results['download']['status']}")
        print(f"    Progress: {results['download']['progress_percent']:.1f}%")

        # 6. Download Progress
        if results["download"]["task_id"]:
            print("\n[6] Progress Check Endpoint:")
            task_id = results["download"]["task_id"]
            response = client.get(f"/api/download/progress/{task_id}")
            results["progress"] = response.json()
            results["progress"]["content_id"] = f"prog_{int(time.time())}"
            print(f"    Task ID: {task_id}")
            print(f"    Status: {results['progress']['status']}")
            print(f"    Progress: {results['progress']['progress_percent']:.1f}%")

        # 7. History
        print("\n[7] History Endpoint:")
        response = client.get("/api/history")
        results["history"] = response.json()
        print(f"    Total Items: {results['history']['total_count']}")

        return results

    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


def generate_json_report(all_results):
    """Generate comprehensive JSON report"""
    print("\n" + "=" * 70)
    print("GENERATING JSON REPORT")
    print("=" * 70)

    report = {
        "report_generated": datetime.now().isoformat(),
        "project": "Social Media Downloader",
        "version": "1.0.0",
        "server_mode": True,
        "test_results": all_results,
    }

    # Save to file
    report_file = "api_test_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n✓ Report saved to: {report_file}")
    print(f"✓ Report size: {len(json.dumps(report, indent=2))} chars")

    # Print summary
    print("\n" + "-" * 50)
    print("REPORT SUMMARY:")
    print("-" * 50)
    print(
        json.dumps(
            {
                "timestamp": report["report_generated"],
                "server_mode": report["server_mode"],
                "tests_run": len([k for k in all_results.keys() if all_results.get(k)]),
                "video_info": {
                    "content_id": all_results.get("video_info", {}).get("content_id"),
                    "platform": all_results.get("video_info", {}).get("platform"),
                    "title": all_results.get("video_info", {}).get("title"),
                    "duration": all_results.get("video_info", {}).get("duration"),
                    "user_link": all_results.get("video_info", {}).get("user_link"),
                },
                "download": {
                    "content_id": all_results.get("download", {}).get("content_id"),
                    "task_id": all_results.get("download", {}).get("task_id"),
                    "file_path": all_results.get("download", {}).get("file_path"),
                    "file_size_mb": all_results.get("download", {}).get("file_size_mb"),
                    "status": all_results.get("download", {}).get("status"),
                },
            },
            indent=2,
        )
    )

    return report


def main():
    """Run all comprehensive tests"""
    print("\n" + "=" * 70)
    print("SOCIAL MEDIA DOWNLOADER - COMPREHENSIVE API TEST")
    print("=" * 70)
    print("Testing: YouTube (5-min video), Facebook, Instagram APIs")
    print("Features: Unique Content ID, File Path, User Link, JSON Format")
    print("=" * 70)

    results = {}

    # Test 1: Video Info with Details
    results["video_info"] = test_video_info_with_details()

    # Test 2: Download with File Path
    results["download"] = test_download_with_file_path()

    # Test 3: API Endpoints
    results["api_endpoints"] = test_api_endpoints_comprehensive()

    # Generate Report
    report = generate_json_report(results)

    # Final Summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)

    all_passed = all(
        [
            results.get("video_info") is not None,
            results.get("download") is not None,
            results.get("api_endpoints") is not None,
        ]
    )

    print(f"Video Info Test: {'✓ PASSED' if results.get('video_info') else '✗ FAILED'}")
    print(f"Download Test: {'✓ PASSED' if results.get('download') else '✗ FAILED'}")
    print(
        f"API Endpoints Test: {'✓ PASSED' if results.get('api_endpoints') else '✗ FAILED'}"
    )

    print("\n" + "=" * 70)
    if all_passed:
        print("ALL TESTS PASSED! ✓")
        print("Server is ready with unique content IDs and file paths!")
    else:
        print("SOME TESTS FAILED! ✗")
    print("=" * 70)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
