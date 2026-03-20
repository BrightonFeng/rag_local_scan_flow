#!/usr/bin/env python3
#
#  Copyright 2025 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import time

import pytest
from video_utils import TEST_VIDEOS, build_messages, extract_frames


@pytest.mark.p1
class TestVideoOllamaParsing:
    """Parametrized video parsing tests via Ollama VLM."""

    @pytest.mark.parametrize("video_path,expected_keyword", TEST_VIDEOS)
    def test_single_video_parse(self, ollama_client, video_path, expected_keyword):
        """Test single run: extract frames, send to VLM, verify non-empty response."""
        frames, total, sizes = extract_frames(video_path)
        assert len(frames) > 0, f"No frames extracted from {video_path}"
        assert sizes and max(sizes) < 200_000, f"Frame too large: {max(sizes)} bytes"

        messages = build_messages(frames)
        start = time.time()
        response = ollama_client.chat(model="qwen3-vl:8b", messages=messages, keep_alive=-1)
        elapsed = time.time() - start

        content = response["message"]["content"].strip()
        print(f"\n  [{video_path.split('/')[-1]}] {elapsed:.1f}s, {len(content)} chars, expected: {expected_keyword}")
        if not content and response["message"].get("thinking"):
            print(f"  Thinking: {response['message']['thinking'][:200]}")

        assert content, f"Empty response for {video_path}"

    @pytest.mark.parametrize("video_path,expected_keyword", TEST_VIDEOS)
    def test_video_stability_10_runs(self, ollama_client, video_path, expected_keyword):
        """Test 10 runs: verify no repetition or empty responses across runs."""
        failures = []
        for run in range(10):
            frames, _, _ = extract_frames(video_path)
            messages = build_messages(frames)
            response = ollama_client.chat(model="qwen3-vl:8b", messages=messages, keep_alive=-1)
            content = response["message"]["content"].strip()

            if not content:
                msg = response["message"].get("thinking", "empty")
                failures.append(f"Run {run + 1}: empty response, thinking={str(msg)[:100]}")
                continue

            words = content.split()
            if len(set(words)) < len(words) * 0.3:
                failures.append(f"Run {run + 1}: possible repetition")

        print(f"\n  [{video_path.split('/')[-1]}] {10 - len(failures)}/10 successful")
        assert not failures, f"Failures: {failures}"
