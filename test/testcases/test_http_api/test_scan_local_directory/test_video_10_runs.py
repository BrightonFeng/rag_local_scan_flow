#!/usr/bin/env python3
"""
Test video frame resizing for Ollama VLM processing.
Run 10 times to verify stability.
"""

import sys

sys.path.insert(0, "/ragflow")
import ollama
import cv2
import base64
import time

files = [
    ("/hdd1/test_scan/test1/091125.mp4", "koala"),  # koala
    ("/hdd1/test_scan/test1/100305.mp4", "lizard"),  # lizard
    ("/hdd1/test_scan/test1/海狮1.mp4", "sea lion"),  # sea lion
    ("/hdd1/test_scan/test1/骑马.mp4", "horse"),  # horse
]

client = ollama.Client(host="http://host.docker.internal:11434")
max_dim = 480

for run in range(10):
    print(f"\n{'#' * 70}")
    print(f"# Run {run + 1}/10")
    print(f"{'#' * 70}")

    all_success = True

    for i, (video_path, desc) in enumerate(files):
        filename = video_path.split("/")[-1]
        print(f"\n--- Video {i + 1}: {filename} ({desc}) ---")

        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        interval = max(1, total_frames // 8)

        frames = []
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_count % interval == 0:
                h, w = frame.shape[:2]
                if h > max_dim or w > max_dim:
                    if h > w:
                        new_h, new_w = max_dim, int(w * max_dim / h)
                    else:
                        new_h, new_w = int(h * max_dim / w), max_dim
                    frame = cv2.resize(frame, (new_w, new_h))
                _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                frames.append(base64.b64encode(buffer).decode("utf-8"))
            frame_count += 1
            if len(frames) >= 8:
                break
        cap.release()

        messages = [{"role": "user", "content": "请详细描述这个视频中正在发生的画面内容。", "images": frames}]

        start_time = time.time()
        try:
            response = client.chat(model="qwen3-vl:8b", messages=messages, keep_alive=-1)
            elapsed = time.time() - start_time

            content = response["message"]["content"].strip()
            if content:
                # Check for repetition or quality issues
                words = content.split()
                # Simple repetition check
                if len(set(words)) < len(words) * 0.3:  # Too much repetition
                    print(f"  [WARNING] Possible repetition detected")
                    all_success = False
                else:
                    print(f"  [OK] {elapsed:.1f}s, {len(content)} chars")
            else:
                if response["message"].get("thinking"):
                    print(f"  [WARNING] Empty response, has thinking: {response['message']['thinking'][:100]}...")
                else:
                    print(f"  [FAIL] Empty response")
                all_success = False
        except Exception as e:
            print(f"  [FAIL] Error: {e}")
            all_success = False

    if all_success:
        print(f"\n>>> Run {run + 1}: ALL SUCCESS")
    else:
        print(f"\n>>> Run {run + 1}: SOME FAILURES")

print(f"\n{'=' * 70}")
print("TEST COMPLETE")
print(f"{'=' * 70}")
