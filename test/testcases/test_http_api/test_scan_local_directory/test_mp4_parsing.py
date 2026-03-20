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
#  distributed under the License is distributed on an "AS IS" BASIS
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import json
import time

import pytest
import requests
from configs import HOST_ADDRESS, VERSION

HOST = HOST_ADDRESS


@pytest.mark.p1
class TestMp4Parsing:
    """End-to-end test: create KB, scan video directory, verify parsing."""

    def test_scan_video_directory_and_wait(self, scan_auth):
        """Create KB, scan video directory, wait for parsing to complete."""
        headers = {"Authorization": str(scan_auth)}

        response = requests.post(f"{HOST}/{VERSION}/kb/create", headers=headers, json={"name": f"test_mp4_{int(time.time())}"}, timeout=30)
        kb_data = response.json()
        assert kb_data.get("code") == 0, f"Failed to create KB: {kb_data}"
        kb_id = kb_data["data"]["kb_id"]
        print(f"\n  KB: {kb_id}")

        test_dir = "/hdd1/test_scan/test1"
        response = requests.post(f"{HOST}/{VERSION}/document/scan_path", headers=headers, json={"kb_id": kb_id, "path": test_dir, "scan_interval": 60}, timeout=30)
        scan_result = response.json()
        assert scan_result.get("code") == 0, f"Scan failed: {scan_result}"
        print(f"  Scan initiated for {test_dir}")

        for i in range(12):
            time.sleep(10)
            response = requests.post(f"{HOST}/{VERSION}/document/list", headers=headers, params={"kb_id": kb_id}, timeout=30)
            docs = response.json()
            if docs.get("code") == 0 and docs.get("data"):
                for doc in docs["data"].get("docs", []):
                    status = doc.get("status")
                    chunk_num = doc.get("chunk_num")
                    name = doc.get("name")
                    print(f"  [{i * 10}s] {name}: status={status}, chunks={chunk_num}")
                    assert status != "failed", f"Document {name} failed. Detail: {requests.get(f'{HOST}/{VERSION}/document/get/{doc["id"]}', headers=headers, timeout=30).json()}"

        requests.delete(f"{HOST}/{VERSION}/kb/{kb_id}", headers=headers, timeout=30)
