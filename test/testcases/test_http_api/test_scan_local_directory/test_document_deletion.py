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


TEST_SCAN_DIR = "/hdd1/test_scan"


@pytest.mark.p1
@pytest.mark.usefixtures("clear_datasets")
class TestDocumentDeletion:
    """Test cases for document deletion with vector index cleanup."""

    def test_delete_file_removes_document_and_chunks(self, HttpApiAuth, add_dataset):
        """Test that deleting a file from scanned directory removes document and its chunks."""
        from conftest import scan_path, list_documents, retrieval_test

        test_subdir = os.path.join(TEST_SCAN_DIR, "delete_test1")
        os.makedirs(test_subdir, exist_ok=True)

        test_file = os.path.join(test_subdir, "delete_test.txt")
        with open(test_file, "w") as f:
            f.write("This file will be deleted KEYWORD123")

        scan_path(HttpApiAuth, add_dataset, test_subdir, scan_interval=60)

        time.sleep(15)

        docs = list_documents(HttpApiAuth, add_dataset)
        assert docs.get("code") == 0, f"list_documents failed: {docs}"
        doc_names = [d["name"] for d in (docs.get("data") or {}).get("docs", [])]
        assert "delete_test.txt" in doc_names, "Document should be created"

        res = retrieval_test(HttpApiAuth, add_dataset, "KEYWORD123")
        assert res.get("code") == 0, f"retrieval_test failed: {res}"
        chunks = (res.get("data") or {}).get("chunks", [])
        assert len(chunks) > 0, "Chunks should exist after initial scan"

        os.remove(test_file)

        time.sleep(15)

        docs = list_documents(HttpApiAuth, add_dataset)
        assert docs.get("code") == 0, f"list_documents failed: {docs}"
        doc_names = [d["name"] for d in (docs.get("data") or {}).get("docs", [])]
        assert "delete_test.txt" not in doc_names, "Document should be deleted after file removal"

    def test_modify_file_reparses_document(self, HttpApiAuth, add_dataset):
        """Test that modifying a file triggers re-parsing and index update."""
        from conftest import scan_path, retrieval_test

        test_subdir = os.path.join(TEST_SCAN_DIR, "delete_test2")
        os.makedirs(test_subdir, exist_ok=True)

        test_file = os.path.join(test_subdir, "modify_test.txt")
        with open(test_file, "w") as f:
            f.write("Original content KEYWORD456")

        scan_path(HttpApiAuth, add_dataset, test_subdir, scan_interval=60)

        time.sleep(15)

        res = retrieval_test(HttpApiAuth, add_dataset, "KEYWORD456")
        assert res.get("code") == 0, f"retrieval_test failed: {res}"
        chunks = (res.get("data") or {}).get("chunks", [])
        assert len(chunks) > 0, "Chunks should exist after initial scan"

        time.sleep(2)

        with open(test_file, "w") as f:
            f.write("Modified content NEWKEYWORD789")

        time.sleep(15)

        res_new = retrieval_test(HttpApiAuth, add_dataset, "NEWKEYWORD789")
        assert res_new.get("code") == 0, f"retrieval_test failed: {res_new}"
        chunks_new = (res_new.get("data") or {}).get("chunks", [])

        assert len(chunks_new) > 0, "New chunks should exist after re-parsing"
        assert chunks_new[0]["content_with_weight"].find("Modified content") >= 0, "Content should be updated"
