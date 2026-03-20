#!/usr/bin/env python3
"""
Video test utilities for RAGFlow local_scan video parsing tests.

Provides shared frame extraction and test video definitions to avoid
code duplication across multiple test scripts.
"""

import base64
import sys
from typing import List, Tuple

sys.path.insert(0, "/ragflow")

cv2 = None

TEST_VIDEOS: List[Tuple[str, str]] = [
    ("/hdd1/test_scan/test1/091125.mp4", "koala"),
    ("/hdd1/test_scan/test1/100305.mp4", "lizard"),
    ("/hdd1/test_scan/test1/海狮1.mp4", "sea lion"),
    ("/hdd1/test_scan/test1/骑马.mp4", "horse"),
]

MAX_DIM = 480
NUM_FRAMES = 8
JPEG_QUALITY = 85
PROMPT = "请详细描述这个视频中正在发生的画面内容。"


def extract_frames(video_path: str, max_dim: int = MAX_DIM, num_frames: int = NUM_FRAMES, jpeg_quality: int = JPEG_QUALITY) -> Tuple[List[str], int, List[int]]:
    """
    Extract frames from a video file and resize them.

    Returns:
        (frames, total_frames, frame_sizes) where frames is a list of
        base64-encoded JPEG images.
    """
    global cv2
    if cv2 is None:
        import cv2 as _cv2

        cv2 = _cv2
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    interval = max(1, total_frames // num_frames)

    frames = []
    frame_sizes = []
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
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
            b64 = base64.b64encode(buffer).decode("utf-8")
            frames.append(b64)
            frame_sizes.append(len(b64))
        frame_count += 1
        if len(frames) >= num_frames:
            break
    cap.release()
    return frames, total_frames, frame_sizes


def build_messages(frames: List[str], prompt: str = PROMPT) -> List[dict]:
    """Build messages payload for Ollama VLM chat."""
    return [{"role": "user", "content": prompt, "images": frames}]
