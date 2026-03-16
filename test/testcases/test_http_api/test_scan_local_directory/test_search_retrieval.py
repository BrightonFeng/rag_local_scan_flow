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

import os
import time

import pytest
import requests
from configs import HOST_ADDRESS, VERSION


RETRIEVAL_TEST_API_URL = f"{HOST_ADDRESS}/{VERSION}/chunk/retrieval_test"
DOCUMENT_API_URL = f"{HOST_ADDRESS}/{VERSION}/document"
SCAN_PATH_API_URL = f"{HOST_ADDRESS}/{VERSION}/document/scan_path"


TEST_SCAN_DIR = "/hdd1/test_scan"


def setup_module(module):
    """Setup test directory."""
    os.makedirs(TEST_SCAN_DIR, exist_ok=True)


def scan_path(auth, kb_id, path, scan_interval=10080):
    """Scan a local directory."""
    headers = {"Authorization": str(auth)}
    payload = {"kb_id": kb_id, "path": path, "scan_interval": scan_interval}
    response = requests.post(SCAN_PATH_API_URL, headers=headers, json=payload)
    return response.json()


def retrieval_test(auth, kb_id, question, page=1, size=10):
    """Perform retrieval test."""
    headers = {"Authorization": str(auth)}
    payload = {"kb_id": kb_id, "question": question, "page": page, "size": size, "highlight": True}
    response = requests.post(RETRIEVAL_TEST_API_URL, headers=headers, json=payload)
    return response.json()


@pytest.mark.p1
@pytest.mark.usefixtures("clear_datasets")
class TestSearchRetrievalLocalScan:
    """Test cases for search retrieval with local scan files."""

    def test_retrieval_returns_source_type_and_location(self, HttpApiAuth, add_dataset):
        """Test that retrieval returns source_type and location for local_scan files."""
        test_subdir = os.path.join(TEST_SCAN_DIR, "retrieval_test1")
        os.makedirs(test_subdir, exist_ok=True)

        test_file = os.path.join(test_subdir, "test_retrieval.txt")
        with open(test_file, "w") as f:
            f.write("This is a test file for retrieval testing with keyword TESTKEY123")

        scan_path(HttpApiAuth, add_dataset, test_subdir, scan_interval=60)

        time.sleep(10)

        res = retrieval_test(HttpApiAuth, add_dataset, "TESTKEY123")

        assert res["code"] == 0, f"Retrieval failed: {res.get('message')}"

        chunks = res.get("data", {}).get("chunks", [])
        assert len(chunks) > 0, "No chunks returned"

        chunk = chunks[0]

        assert "source_type" in chunk, "source_type field missing from chunk"
        assert "location" in chunk, "location field missing from chunk"

        assert chunk["source_type"] == "local_scan", f"Expected source_type 'local_scan', got '{chunk['source_type']}'"
        assert chunk["location"] is not None, "location should not be None"
        assert test_subdir in chunk["location"], f"Expected location to contain '{test_subdir}', got '{chunk['location']}'"

    def test_retrieval_full_path_display(self, HttpApiAuth, add_dataset):
        """Test that full path is returned for local_scan files."""
        test_subdir = os.path.join(TEST_SCAN_DIR, "retrieval_test2")
        os.makedirs(test_subdir, exist_ok=True)

        test_file = os.path.join(test_subdir, "nested_test.txt")
        with open(test_file, "w") as f:
            f.write("Testing full path display with keyword FULLPATH456")

        scan_path(HttpApiAuth, add_dataset, test_subdir, scan_interval=60)

        time.sleep(10)

        res = retrieval_test(HttpApiAuth, add_dataset, "FULLPATH456")

        assert res["code"] == 0, f"Retrieval failed: {res.get('message')}"

        chunks = res.get("data", {}).get("chunks", [])
        assert len(chunks) > 0, "No chunks returned"

        chunk = chunks[0]

        full_path = chunk.get("location", "")
        assert full_path.endswith("nested_test.txt"), f"Expected path to end with 'nested_test.txt', got '{full_path}'"
        assert "/retrieval_test2/" in full_path, f"Expected path to contain '/retrieval_test2/', got '{full_path}'"
