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
from video_utils import TEST_VIDEOS

from common import settings

settings.init_settings()

try:
    from rag.app.picture import chunk
except ImportError:
    chunk = None


TENANT_ID = "6f020496203111f1a9ee414ccff73856"


def callback(prog, msg):
    print(f"  Progress: {prog}, Message: {msg}")


@pytest.mark.p1
class TestVideoChunkParsing:
    """Test video parsing through rag.app.picture.chunk."""

    @pytest.mark.parametrize("video_path,_desc", TEST_VIDEOS)
    def test_video_chunk(self, configure_ollama_img2txt, video_path, _desc):
        """Test that rag.app.picture.chunk successfully parses each video."""
        if chunk is None:
            pytest.skip("rag.app.picture not importable (requires full RAGFlow backend)")

        filename = video_path.split("/")[-1]
        print(f"\n  Testing {filename}")

        with open(video_path, "rb") as f:
            video_bytes = f.read()
        print(f"  File size: {len(video_bytes) / 1024 / 1024:.1f} MB")

        start = time.time()
        result = chunk(filename, video_bytes, TENANT_ID, "Chinese", callback=callback)
        elapsed = time.time() - start

        assert result, f"Failed to parse {filename}"
        doc = result[0]
        print(f"  Parsed in {elapsed:.1f}s, title: {doc.get('title_tks', '')[:100]}")
