#!/usr/bin/env python3
import sys

sys.path.insert(0, "/ragflow")
from rag.app.picture import chunk
import time

tenant_id = "6f020496203111f1a9ee414ccff73856"

files = [
    "/hdd1/test_scan/test1/091125.mp4",  # koala
    "/hdd1/test_scan/test1/100305.mp4",  # lizard
    "/hdd1/test_scan/test1/海狮1.mp4",  # sea lion
    "/hdd1/test_scan/test1/骑马.mp4",  # horse
]

for i, video_path in enumerate(files):
    filename = video_path.split("/")[-1]
    print(f"\n{'=' * 60}")
    print(f"Video {i + 1}: {filename}")
    print("=" * 60)

    with open(video_path, "rb") as f:
        video_bytes = f.read()
    print(f"File size: {len(video_bytes) / 1024 / 1024:.1f} MB")

    def callback(prog, msg):
        print(f"  Progress: {prog}, Message: {msg}")

    start_time = time.time()
    try:
        result = chunk(filename, video_bytes, tenant_id, "Chinese", callback=callback)
        elapsed = time.time() - start_time

        if result:
            print(f"\n  Parsed successfully in {elapsed:.1f}s")
            doc = result[0]
            # Try to get parsed content from the doc
            content = doc.get("docnm_kwd", "")
            # The actual content is in the tokenizer output
            # Let's check the tokenize result
            print(f"  Title tokens: {doc.get('title_tks', '')[:100]}")
        else:
            print(f"\n  Failed - no result returned")
    except Exception as e:
        print(f"\n  Error: {e}")
        import traceback

        traceback.print_exc()
