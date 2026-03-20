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

import pytest


TEST_SCAN_DIR = "/hdd1/test_scan"


@pytest.mark.p1
@pytest.mark.usefixtures("clear_datasets")
class TestScanLocalDirectory:
    """Test cases for scan local directory feature."""

    def test_scan_path_without_auth(self):
        """Test scanning without authentication should fail."""
        res = pytest.importorskip("requests").post(
            f"{pytest.importorskip('configs').HOST_ADDRESS}/v1/document/scan_path",
            json={"kb_id": "kb_id", "path": "/tmp/test"},
        )
        assert res.json()["code"] != 0

    def test_scan_path_invalid_path(self, HttpApiAuth, add_dataset):
        """Test scanning with invalid path should fail."""
        from conftest import scan_path

        res = scan_path(HttpApiAuth, add_dataset, "/nonexistent/path/12345")
        assert res["code"] != 0

    def test_scan_path_valid_directory(self, HttpApiAuth, add_dataset):
        """Test scanning a valid directory with files."""
        from conftest import scan_path, list_documents

        test_subdir = os.path.join(TEST_SCAN_DIR, "test1")
        os.makedirs(test_subdir, exist_ok=True)

        test_file = os.path.join(test_subdir, "test.txt")
        with open(test_file, "w") as f:
            f.write("Hello World")

        res = scan_path(HttpApiAuth, add_dataset, test_subdir, scan_interval=60)
        assert res.get("code") == 0, f"Scan failed: {res}"

        docs = list_documents(HttpApiAuth, add_dataset)
        assert docs.get("code") == 0, f"list_documents failed: {docs}"
        doc_names = [d["name"] for d in (docs.get("data") or {}).get("docs", [])]
        assert "test.txt" in doc_names

    def test_get_scanned_directories(self, HttpApiAuth, add_dataset):
        """Test getting scanned directories."""
        from conftest import scan_path, get_scanned_directories

        test_subdir = os.path.join(TEST_SCAN_DIR, "test2")
        os.makedirs(test_subdir, exist_ok=True)

        test_file = os.path.join(test_subdir, "test2.txt")
        with open(test_file, "w") as f:
            f.write("Test content")

        scan_path(HttpApiAuth, add_dataset, test_subdir, scan_interval=10080)

        res = get_scanned_directories(HttpApiAuth, add_dataset)
        assert res.get("code") == 0, f"get_scanned_directories failed: {res}"
        assert (res.get("data") or []) and len(res["data"]) > 0

    def test_scan_interval_update(self, HttpApiAuth, add_dataset):
        """Test updating scan interval."""
        from conftest import scan_path, get_scanned_directories, update_scan_interval

        test_subdir = os.path.join(TEST_SCAN_DIR, "test3")
        os.makedirs(test_subdir, exist_ok=True)

        test_file = os.path.join(test_subdir, "test3.txt")
        with open(test_file, "w") as f:
            f.write("Test content 3")

        scan_path(HttpApiAuth, add_dataset, test_subdir, scan_interval=60)

        dirs = get_scanned_directories(HttpApiAuth, add_dataset)
        assert dirs.get("code") == 0, f"get_scanned_directories failed: {dirs}"
        assert dirs.get("data"), f"No scanned directories found: {dirs}"
        dir_id = dirs["data"][0]["id"]

        res = update_scan_interval(HttpApiAuth, dir_id, 30)
        assert res["code"] == 0

    def test_sync_deleted_file(self, HttpApiAuth, add_dataset):
        """Test that deleted files are removed from database."""
        from conftest import scan_path, list_documents

        test_subdir = os.path.join(TEST_SCAN_DIR, "test4")
        os.makedirs(test_subdir, exist_ok=True)

        test_file = os.path.join(test_subdir, "test4.txt")
        with open(test_file, "w") as f:
            f.write("Test content 4")

        scan_path(HttpApiAuth, add_dataset, test_subdir, scan_interval=60)

        docs = list_documents(HttpApiAuth, add_dataset)
        assert docs.get("code") == 0, f"list_documents failed: {docs}"
        doc_names_before = [d["name"] for d in (docs.get("data") or {}).get("docs", [])]
        assert "test4.txt" in doc_names_before

        os.remove(test_file)

        scan_path(HttpApiAuth, add_dataset, test_subdir, scan_interval=60)

        docs = list_documents(HttpApiAuth, add_dataset)
        doc_names_after = [d["name"] for d in docs.get("data", {}).get("docs", [])]
        assert "test4.txt" not in doc_names_after
