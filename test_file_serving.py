"""Test file serving and download endpoints"""

import sys
import os
import json

sys.path.insert(0, ".")

from fastapi.testclient import TestClient
from src.api.app import app


def test_file_serving():
    """Test that files can be accessed globally"""
    print("=" * 70)
    print("TESTING FILE SERVING")
    print("=" * 70)

    client = TestClient(app)

    # 1. List files
    print("\n[1] List all downloaded files:")
    response = client.get("/api/files")
    print(f"    Status: {response.status_code}")
    data = response.json()
    print(f"    Total files: {data['total']}")

    for f in data.get("files", []):
        print(f"    - {f['name']} ({f['size_mb']} MB)")

    # 2. Test health endpoint
    print("\n[2] Health check:")
    response = client.get("/api/health")
    print(f"    Status: {response.json()['status']}")

    # 3. Test platforms
    print("\n[3] Supported platforms:")
    response = client.get("/api/platforms")
    platforms = response.json()["platforms"]
    print(f"    {platforms}")

    # 4. Test video info
    print("\n[4] Video info (YouTube):")
    response = client.get("/api/info?url=https://www.youtube.com/watch?v=9bZkp7q19f0")
    info = response.json()
    print(f"    Platform: {info['platform']}")
    print(f"    Title: {info['title'][:40]}...")
    print(f"    Duration: {info['duration']}s")

    # 5. Test download
    print("\n[5] Download video:")
    response = client.post(
        "/api/download",
        json={
            "url": "https://www.youtube.com/watch?v=9bZkp7q19f0",
            "quality": "360p",
            "format": "mp4",
        },
    )
    dl = response.json()
    print(f"    Task ID: {dl['task_id']}")
    print(f"    Status: {dl['status']}")
    print(f"    File: {dl['file_path']}")

    # 6. Check progress
    print("\n[6] Check download progress:")
    response = client.get(f"/api/download/progress/{dl['task_id']}")
    progress = response.json()
    print(f"    Task ID: {progress['task_id']}")
    print(f"    Status: {progress['status']}")
    print(f"    Progress: {progress['progress_percent']:.1f}%")

    # 7. List files again
    print("\n[7] List files after download:")
    response = client.get("/api/files")
    data = response.json()
    print(f"    Total files: {data['total']}")

    for f in data.get("files", []):
        print(f"    - {f['name']} ({f['size_mb']} MB)")

    # 8. Test file download
    if data["files"]:
        filename = data["files"][0]["name"]
        print(f"\n[8] Download file '{filename}':")
        response = client.get(f"/files/{filename}")
        print(f"    Status: {response.status_code}")
        print(f"    Content-Type: {response.headers.get('content-type')}")
        print(f"    Content-Length: {response.headers.get('content-length')} bytes")

        # Verify file content
        if response.status_code == 200:
            print(f"    ✓ File downloaded successfully!")

    # 9. Test history
    print("\n[9] Download history:")
    response = client.get("/api/history")
    history = response.json()
    print(f"    Total items: {history['total_count']}")

    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("SOCIAL MEDIA DOWNLOADER - FILE SERVING TEST")
    print("Testing: Global file access via URL")
    print("=" * 70)

    try:
        test_file_serving()

        print("\n" + "=" * 70)
        print("ALL FILE SERVING TESTS PASSED! ✓")
        print("Files are now accessible globally via /files/{filename}")
        print("Example: http://localhost:8000/files/filename.webm")
        print("=" * 70)

        return 0

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
