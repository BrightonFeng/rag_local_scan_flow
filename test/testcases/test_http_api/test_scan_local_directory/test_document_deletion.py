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
SCANNED_DIRS_API_URL = f"{HOST_ADDRESS}/{VERSION}/document/scanned_directories"


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


def list_documents(auth, kb_id):
    """List documents in a knowledge base."""
    headers = {"Authorization": str(auth)}
    response = requests.get(DOCUMENT_API_URL, headers=headers, params={"kb_id": kb_id})
    return response.json()


def retrieval_test(auth, kb_id, question, page=1, size=10):
    """Perform retrieval test."""
    headers = {"Authorization": str(auth)}
    payload = {"kb_id": kb_id, "question": question, "page": page, "size": size, "highlight": True}
    response = requests.post(RETRIEVAL_TEST_API_URL, headers=headers, json=payload)
    return response.json()


@pytest.mark.p1
@pytest.mark.usefixtures("clear_datasets")
class TestDocumentDeletion:
    """Test cases for document deletion with vector index cleanup."""

    def test_delete_file_removes_document_and_chunks(self, HttpApiAuth, add_dataset):
        """Test that deleting a file from scanned directory removes document and its chunks."""
        test_subdir = os.path.join(TEST_SCAN_DIR, "delete_test1")
        os.makedirs(test_subdir, exist_ok=True)

        test_file = os.path.join(test_subdir, "delete_test.txt")
        with open(test_file, "w") as f:
            f.write("This file will be deleted KEYWORD123")

        scan_path(HttpApiAuth, add_dataset, test_subdir, scan_interval=60)

        time.sleep(15)

        docs = list_documents(HttpApiAuth, add_dataset)
        doc_names = [d["name"] for d in docs.get("data", {}).get("docs", [])]
        assert "delete_test.txt" in doc_names, "Document should be created"

        res = retrieval_test(HttpApiAuth, add_dataset, "KEYWORD123")
        assert res["code"] == 0
        chunks = res.get("data", {}).get("chunks", [])
        assert len(chunks) > 0, "Chunks should exist after initial scan"

        os.remove(test_file)

        time.sleep(15)

        docs = list_documents(HttpApiAuth, add_dataset)
        doc_names = [d["name"] for d in docs.get("data", {}).get("docs", [])]
        assert "delete_test.txt" not in doc_names, "Document should be deleted after file removal"

    def test_modify_file_reparses_document(self, HttpApiAuth, add_dataset):
        """Test that modifying a file triggers re-parsing and index update."""
        test_subdir = os.path.join(TEST_SCAN_DIR, "delete_test2")
        os.makedirs(test_subdir, exist_ok=True)

        test_file = os.path.join(test_subdir, "modify_test.txt")
        with open(test_file, "w") as f:
            f.write("Original content KEYWORD456")

        scan_path(HttpApiAuth, add_dataset, test_subdir, scan_interval=60)

        time.sleep(15)

        res = retrieval_test(HttpApiAuth, add_dataset, "KEYWORD456")
        assert res["code"] == 0
        chunks = res.get("data", {}).get("chunks", [])
        assert len(chunks) > 0, "Chunks should exist after initial scan"

        time.sleep(2)

        with open(test_file, "w") as f:
            f.write("Modified content NEWKEYWORD789")

        time.sleep(15)

        res_old = retrieval_test(HttpApiAuth, add_dataset, "KEYWORD456")
        chunks_old = res_old.get("data", {}).get("chunks", [])

        res_new = retrieval_test(HttpApiAuth, add_dataset, "NEWKEYWORD789")
        chunks_new = res_new.get("data", {}).get("chunks", [])

        assert len(chunks_new) > 0, "New chunks should exist after re-parsing"
        assert chunks_new[0]["content_with_weight"].find("Modified content") >= 0, "Content should be updated"
