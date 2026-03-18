#!/usr/bin/env python3
"""
Test video frame resizing for Ollama VLM processing.

This script tests that video frames are properly resized before being sent to the
Ollama vision-language model for description. The max_dim threshold affects:
- Frame size (larger = more detail but slower processing)
- Processing time (larger frames = longer VLM inference)
- Output quality (too small = loss of detail)

Current threshold: 320px (frames ~30KB each, 8 frames total ~240KB)
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

for i, (video_path, desc) in enumerate(files):
    filename = video_path.split("/")[-1]
    print(f"\n{'=' * 60}")
    print(f"Video {i + 1}: {filename} ({desc})")
    print("=" * 60)

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
            max_dim = 480
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

    print(f"Total frames: {total_frames}, Extracted: {len(frames)}")
    print(f"Frame sizes: {[len(f) for f in frames]}")

    messages = [{"role": "user", "content": "请详细描述这个视频中正在发生的画面内容。", "images": frames}]

    print("Sending to Ollama...")
    start_time = time.time()
    try:
        response = client.chat(model="qwen3-vl:8b", messages=messages, keep_alive=-1)
        elapsed = time.time() - start_time

        content = response["message"]["content"].strip()
        print(f"\nResponse ({elapsed:.1f}s):")
        print(content[:1500] if content else "EMPTY")

        if not content and response["message"].get("thinking"):
            thinking = response["message"]["thinking"].strip()
            print(f"\nThinking (first 500 chars):")
            print(thinking[:500])
    except Exception as e:
        print(f"Error: {e}")
