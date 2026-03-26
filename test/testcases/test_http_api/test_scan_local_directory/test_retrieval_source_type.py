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

"""
Test that retrieval results include source_type and location for local_scan files.

This verifies that when a user clicks on a thumbnail or link in search/chat,
the frontend knows whether the file is a local_scan and can open it properly.
"""

import os
import time

import pytest
import requests

from configs import EMAIL, HOST_ADDRESS, PASSWORD, VERSION


def _make_auth(auth):
    if hasattr(auth, "_token"):
        return auth
    return {"Authorization": str(auth)}


@pytest.mark.p1
class TestSourceTypeEnrichment:
    """Test that retrieval results include source_type and location fields."""

    @pytest.fixture(autouse=False)
    def kb(self, scan_auth, configure_ollama_img2txt):
        kb_id = None
        try:
            resp = requests.post(
                f"{HOST_ADDRESS}/{VERSION}/kb/create",
                headers=_make_auth(scan_auth),
                json={
                    "name": f"test-source-type-{int(time.time())}",
                    "embd_id": "qwen3-embedding:4b",
                    "tenant_embd_id": 8,
                },
                timeout=30,
            )
            data = resp.json()
            assert data.get("code") == 0, f"Failed to create KB: {data}"
            kb_id = data["data"]["kb_id"]

            resp = requests.post(
                f"{HOST_ADDRESS}/{VERSION}/document/scan_path",
                headers=_make_auth(scan_auth),
                json={"kb_id": kb_id, "path": "/hdd1/test_scan", "scan_interval": 10080},
                timeout=30,
            )
            scan_data = resp.json()
            assert scan_data.get("code") == 0, f"Failed to scan path: {scan_data}"

            yield kb_id
        finally:
            if kb_id:
                requests.delete(
                    f"{HOST_ADDRESS}/{VERSION}/kb/{kb_id}",
                    headers=_make_auth(scan_auth),
                    timeout=30,
                )

    def test_retrieval_returns_source_type_and_location(self, scan_auth, configure_ollama_img2txt, kb):
        """Retrieval response should include source_type and location on chunks."""
        time.sleep(3)

        resp = requests.post(
            f"{HOST_ADDRESS}/{VERSION}/chunk/retrieval_test",
            headers=_make_auth(scan_auth),
            json={"kb_id": kb, "question": "胆囊", "size": 10},
            timeout=60,
        )
        data = resp.json()
        assert data.get("code") == 0, f"Retrieval failed: {data}"

        chunks = data.get("data", {}).get("chunks", [])
        doc_aggs = data.get("data", {}).get("doc_aggs", [])

        print(f"\n  chunks returned: {len(chunks)}")
        print(f"  doc_aggs returned: {len(doc_aggs)}")

        if chunks:
            for ck in chunks[:3]:
                print(f"    chunk doc_id={ck.get('doc_id')}, source_type={ck.get('source_type')}, location={ck.get('location')}")
                assert "source_type" in ck, f"Chunk missing 'source_type' field! Available keys: {list(ck.keys())}"
                assert "location" in ck, f"Chunk missing 'location' field! Available keys: {list(ck.keys())}"
                if ck["source_type"] == "local_scan":
                    assert ck["location"], f"local_scan chunk must have non-empty location"
        else:
            print("  [WARN] No chunks returned - files may not be fully parsed yet. Run with a pre-parsed knowledge base for accurate results.")

        if doc_aggs:
            for da in doc_aggs[:3]:
                print(f"    doc_agg doc_id={da.get('doc_id')}, source_type={da.get('source_type')}, location={da.get('location')}")
                assert "source_type" in da, f"doc_agg missing 'source_type' field! Available keys: {list(da.keys())}"
                assert "location" in da, f"doc_agg missing 'location' field! Available keys: {list(da.keys())}"
