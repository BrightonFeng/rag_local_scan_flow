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
import shutil
import time

import pytest
import requests
from configs import HOST_ADDRESS, VERSION


DOCUMENT_API_URL = f"{HOST_ADDRESS}/{VERSION}/document"
SCAN_PATH_API_URL = f"{HOST_ADDRESS}/{VERSION}/document/scan_path"
SCANNED_DIRS_API_URL = f"{HOST_ADDRESS}/{VERSION}/document/scanned_directories"


TEST_SCAN_DIR = "/hdd1/test_scan"


def setup_module(module):
    """Setup test directory."""
    os.makedirs(TEST_SCAN_DIR, exist_ok=True)


def teardown_module(module):
    """Cleanup test directory."""
    if os.path.exists(TEST_SCAN_DIR):
        shutil.rmtree(TEST_SCAN_DIR)


def scan_path(auth, kb_id, path, scan_interval=10080):
    """Scan a local directory."""
    headers = {"Authorization": str(auth)}
    payload = {"kb_id": kb_id, "path": path, "scan_interval": scan_interval}
    response = requests.post(SCAN_PATH_API_URL, headers=headers, json=payload)
    return response.json()


def get_scanned_directories(auth, kb_id):
    """Get all scanned directories for a knowledge base."""
    headers = {"Authorization": str(auth)}
    response = requests.get(SCANNED_DIRS_API_URL, headers=headers, params={"kb_id": kb_id})
    return response.json()


def list_documents(auth, kb_id):
    """List documents in a knowledge base."""
    headers = {"Authorization": str(auth)}
    response = requests.get(DOCUMENT_API_URL, headers=headers, params={"kb_id": kb_id})
    return response.json()


def update_scan_interval(auth, dir_id, scan_interval):
    """Update scan interval for a scanned directory."""
    headers = {"Authorization": str(auth)}
    response = requests.put(f"{SCANNED_DIRS_API_URL}/{dir_id}", headers=headers, json={"scan_interval": scan_interval})
    return response.json()


@pytest.mark.p1
@pytest.mark.usefixtures("clear_datasets")
class TestScanLocalDirectory:
    """Test cases for scan local directory feature."""

    def test_scan_path_without_auth(self):
        """Test scanning without authentication should fail."""
        res = scan_path(None, "kb_id", "/tmp/test")
        assert res["code"] != 0

    def test_scan_path_invalid_path(self, HttpApiAuth, add_dataset):
        """Test scanning with invalid path should fail."""
        res = scan_path(HttpApiAuth, add_dataset, "/nonexistent/path/12345")
        assert res["code"] != 0

    def test_scan_path_valid_directory(self, HttpApiAuth, add_dataset):
        """Test scanning a valid directory with files."""
        test_subdir = os.path.join(TEST_SCAN_DIR, "test1")
        os.makedirs(test_subdir, exist_ok=True)

        test_file = os.path.join(test_subdir, "test.txt")
        with open(test_file, "w") as f:
            f.write("Hello World")

        res = scan_path(HttpApiAuth, add_dataset, test_subdir, scan_interval=60)
        assert res["code"] == 0, f"Scan failed: {res.get('message')}"

        docs = list_documents(HttpApiAuth, add_dataset)
        doc_names = [d["name"] for d in docs.get("data", {}).get("docs", [])]
        assert "test.txt" in doc_names

    def test_get_scanned_directories(self, HttpApiAuth, add_dataset):
        """Test getting scanned directories."""
        test_subdir = os.path.join(TEST_SCAN_DIR, "test2")
        os.makedirs(test_subdir, exist_ok=True)

        test_file = os.path.join(test_subdir, "test2.txt")
        with open(test_file, "w") as f:
            f.write("Test content")

        scan_path(HttpApiAuth, add_dataset, test_subdir, scan_interval=10080)

        res = get_scanned_directories(HttpApiAuth, add_dataset)
        assert res["code"] == 0
        assert len(res["data"]) > 0

    def test_scan_interval_update(self, HttpApiAuth, add_dataset):
        """Test updating scan interval."""
        test_subdir = os.path.join(TEST_SCAN_DIR, "test3")
        os.makedirs(test_subdir, exist_ok=True)

        test_file = os.path.join(test_subdir, "test3.txt")
        with open(test_file, "w") as f:
            f.write("Test content 3")

        scan_path(HttpApiAuth, add_dataset, test_subdir, scan_interval=60)

        dirs = get_scanned_directories(HttpApiAuth, add_dataset)
        dir_id = dirs["data"][0]["id"]

        res = update_scan_interval(HttpApiAuth, dir_id, 30)
        assert res["code"] == 0

    def test_sync_deleted_file(self, HttpApiAuth, add_dataset):
        """Test that deleted files are removed from database."""
        test_subdir = os.path.join(TEST_SCAN_DIR, "test4")
        os.makedirs(test_subdir, exist_ok=True)

        test_file = os.path.join(test_subdir, "test4.txt")
        with open(test_file, "w") as f:
            f.write("Test content 4")

        scan_path(HttpApiAuth, add_dataset, test_subdir, scan_interval=60)

        docs = list_documents(HttpApiAuth, add_dataset)
        doc_names_before = [d["name"] for d in docs.get("data", {}).get("docs", [])]
        assert "test4.txt" in doc_names_before

        os.remove(test_file)

        scan_path(HttpApiAuth, add_dataset, test_subdir, scan_interval=60)

        docs = list_documents(HttpApiAuth, add_dataset)
        doc_names_after = [d["name"] for d in docs.get("data", {}).get("docs", [])]
        assert "test4.txt" not in doc_names_after
