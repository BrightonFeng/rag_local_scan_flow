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
Full integration test for local_scan retrieval flow.

Tests:
1. Create KB + scan /hdd1/test_scan/
2. Wait for parsing, verify results contain expected keywords
3. Search page: retrieval returns source_type + location
4. Chat page: chat response has source_type + location in reference
"""

import time

import pytest

from configs import HOST_ADDRESS, VERSION


def _make_auth(auth):
    if hasattr(auth, "_token"):
        return auth
    return {"Authorization": str(auth)}


@pytest.mark.p1
class TestLocalScanRetrievalFlow:
    """Full flow test for local_scan retrieval + frontend display."""

    @pytest.fixture(autouse=False)
    def kb(self, scan_auth, configure_ollama_img2txt):
        """Create KB with /hdd1/test_scan/ path."""
        import requests

        kb_id = None
        try:
            resp = requests.post(
                f"{HOST_ADDRESS}/{VERSION}/kb/create",
                headers=_make_auth(scan_auth),
                json={
                    "name": f"test-local-scan-{int(time.time())}",
                    "embd_id": "qwen3-embedding:4b",
                    "tenant_embd_id": 8,
                },
                timeout=30,
            )
            data = resp.json()
            assert data.get("code") == 0, f"Failed to create KB: {data}"
            kb_id = data["data"]["kb_id"]
            print(f"\n  Created KB: {kb_id}")

            resp = requests.post(
                f"{HOST_ADDRESS}/{VERSION}/document/scan_path",
                headers=_make_auth(scan_auth),
                json={"kb_id": kb_id, "path": "/hdd1/test_scan", "scan_interval": 10080},
                timeout=30,
            )
            scan_data = resp.json()
            assert scan_data.get("code") == 0, f"Failed to scan path: {scan_data}"
            print(f"  Scan initiated: {scan_data.get('message')}")

            yield kb_id
        finally:
            if kb_id:
                requests.delete(
                    f"{HOST_ADDRESS}/{VERSION}/kb/{kb_id}",
                    headers=_make_auth(scan_auth),
                    timeout=30,
                )
                print(f"\n  Cleaned up KB: {kb_id}")

    @pytest.fixture(autouse=False)
    def dialog_and_conv(self, scan_auth, kb):
        """Create dialog with KB and start a conversation."""
        import requests

        dialog_id = None
        conv_id = f"conv-{int(time.time() * 1000)}"

        try:
            # Create dialog
            resp = requests.post(
                f"{HOST_ADDRESS}/{VERSION}/dialog/set",
                headers=_make_auth(scan_auth),
                json={
                    "name": f"test-chat-{int(time.time())}",
                    "kb_ids": [kb],
                    "prompt_config": {
                        "system": "You are a helpful assistant. Use the following knowledge to answer questions: {knowledge}",
                        "parameters": [{"key": "knowledge", "optional": False}],
                    },
                    "top_n": 6,
                    "top_k": 1024,
                    "similarity_threshold": 0.1,
                    "vector_similarity_weight": 0.3,
                },
                timeout=30,
            )
            data = resp.json()
            assert data.get("code") == 0, f"Failed to create dialog: {data}"
            dialog_id = data["data"]["id"]
            print(f"\n  Created dialog: {dialog_id}")

            # Create conversation
            resp = requests.post(
                f"{HOST_ADDRESS}/{VERSION}/conversation/set",
                headers=_make_auth(scan_auth),
                json={"dialog_id": dialog_id, "conversation_id": conv_id, "is_new": True},
                timeout=30,
            )
            conv_data = resp.json()
            print(f"  Created conversation: {conv_data.get('code')}")

            yield {"dialog_id": dialog_id, "conversation_id": conv_id}

        finally:
            pass  # Dialog cleanup is handled by kb fixture

    def _poll_documents(self, scan_auth, kb_id, timeout=180):
        """Poll until documents appear in KB."""
        import requests

        deadline = time.time() + timeout
        while time.time() < deadline:
            resp = requests.post(
                f"{HOST_ADDRESS}/{VERSION}/document/list",
                headers=_make_auth(scan_auth),
                params={"kb_id": kb_id},
                json={},
                timeout=30,
            )
            data = resp.json()
            docs = data.get("data", {}).get("docs", []) if data.get("code") == 0 else []
            print(f"    [{int(time.time() % 1000):3d}s] Documents: {len(docs)}")
            if docs:
                return docs
            time.sleep(10)
        return []

    def _wait_doc_parsed(self, scan_auth, kb_id, doc_name, timeout=300):
        """Poll until a specific document is fully parsed."""
        import requests

        deadline = time.time() + timeout
        while time.time() < deadline:
            resp = requests.post(
                f"{HOST_ADDRESS}/{VERSION}/document/list",
                headers=_make_auth(scan_auth),
                params={"kb_id": kb_id},
                json={},
                timeout=30,
            )
            data = resp.json()
            if data.get("code") != 0:
                time.sleep(5)
                continue
            docs = data.get("data", {}).get("docs", [])
            for doc in docs:
                if doc.get("name") == doc_name:
                    chunk_num = doc.get("chunk_num", 0)
                    print(f"    [{int(time.time() % 1000):3d}s] {doc_name}: chunk_num={chunk_num}")
                    if chunk_num > 0:
                        return doc
            time.sleep(10)
        return None

    def test_step1_scan_and_parse(self, scan_auth, configure_ollama_img2txt, kb):
        """Step 1: Scan path and verify documents appear."""
        print(f"\n=== Step 1: Scan and Parse ===")
        docs = self._poll_documents(scan_auth, kb, timeout=60)
        assert len(docs) >= 5, f"Expected >=5 documents, got {len(docs)}"
        doc_names = [d.get("name") for d in docs]
        print(f"  Documents: {doc_names}")
        assert "骑马.mp4" in doc_names, f"骑马.mp4 not found"
        assert "2014胆囊.jpg" in doc_names, f"2014胆囊.jpg not found"
        print(f"  PASS: Target documents found")

    def test_step2_parsing_results(self, scan_auth, configure_ollama_img2txt, kb):
        """Step 2: Verify parsing results contain expected keywords."""
        print(f"\n=== Step 2: Parsing Results ===")

        mp4_doc = self._wait_doc_parsed(scan_auth, kb, "骑马.mp4", timeout=300)
        assert mp4_doc is not None, "骑马.mp4 not parsed after 5 minutes"
        assert mp4_doc["chunk_num"] > 0
        print(f"  骑马.mp4: parsed ({mp4_doc['chunk_num']} chunks)")

        jpg_doc = self._wait_doc_parsed(scan_auth, kb, "2014胆囊.jpg", timeout=300)
        assert jpg_doc is not None, "2014胆囊.jpg not parsed after 5 minutes"
        assert jpg_doc["chunk_num"] > 0
        print(f"  2014胆囊.jpg: parsed ({jpg_doc['chunk_num']} chunks)")

    def test_step3_search_retrieval(self, scan_auth, configure_ollama_img2txt, kb):
        """Step 3: Retrieval returns source_type and location on chunks and doc_aggs."""
        import requests

        print(f"\n=== Step 3: Search Retrieval ===")

        jpg_doc = self._wait_doc_parsed(scan_auth, kb, "2014胆囊.jpg", timeout=300)
        assert jpg_doc is not None, "2014胆囊.jpg not parsed"

        resp = requests.post(
            f"{HOST_ADDRESS}/{VERSION}/chunk/retrieval_test",
            headers=_make_auth(scan_auth),
            json={"kb_id": kb, "question": "胆囊", "size": 10},
            timeout=60,
        )
        data = resp.json()
        print(f"  Retrieval: code={data.get('code')}, msg={data.get('message')}")
        assert data.get("code") == 0, f"Retrieval failed: {data}"

        chunks = data.get("data", {}).get("chunks", [])
        doc_aggs = data.get("data", {}).get("doc_aggs", [])
        print(f"  Chunks: {len(chunks)}, DocAggs: {len(doc_aggs)}")

        for c in chunks:
            did = c.get("doc_id", "")[:30]
            st = c.get("source_type")
            loc = c.get("location")
            print(f"    chunk: doc_id={did}..., source_type={st}, location={loc}")
            assert "source_type" in c, f"Chunk missing source_type! Keys: {list(c.keys())}"
            assert "location" in c, f"Chunk missing location! Keys: {list(c.keys())}"

        for d in doc_aggs:
            did = d.get("doc_id", "")[:30]
            st = d.get("source_type")
            loc = d.get("location")
            print(f"    doc_agg: doc_id={did}..., source_type={st}, location={loc}")
            assert "source_type" in d, f"doc_agg missing source_type! Keys: {list(d.keys())}"
            assert "location" in d, f"doc_agg missing location! Keys: {list(d.keys())}"

        print(f"  PASS: All chunks and doc_aggs have source_type and location")

    def test_step4_chat(self, scan_auth, configure_ollama_img2txt, kb):
        """Step 4: Chat response reference includes source_type and location."""
        import requests

        print(f"\n=== Step 4: Chat ===")

        jpg_doc = self._wait_doc_parsed(scan_auth, kb, "2014胆囊.jpg", timeout=300)
        assert jpg_doc is not None, "2014胆囊.jpg not parsed"

        # Create dialog
        resp = requests.post(
            f"{HOST_ADDRESS}/{VERSION}/dialog/set",
            headers=_make_auth(scan_auth),
            json={
                "name": f"test-chat-{int(time.time())}",
                "kb_ids": [kb],
                "prompt_config": {
                    "system": "You are a helpful assistant. Use the following knowledge: {knowledge}",
                    "parameters": [{"key": "knowledge", "optional": False}],
                },
                "top_n": 6,
                "top_k": 1024,
                "similarity_threshold": 0.1,
                "vector_similarity_weight": 0.3,
            },
            timeout=30,
        )
        data = resp.json()
        assert data.get("code") == 0, f"Failed to create dialog: {data}"
        dialog_id = data["data"]["id"]
        conv_id = f"conv-{int(time.time() * 1000)}"
        print(f"  Created dialog: {dialog_id}")

        # Create conversation
        resp = requests.post(
            f"{HOST_ADDRESS}/{VERSION}/conversation/set",
            headers=_make_auth(scan_auth),
            json={"dialog_id": dialog_id, "conversation_id": conv_id, "is_new": True},
            timeout=30,
        )
        print(f"  Conversation: {resp.json().get('code')}")

        # Chat (non-streaming)
        resp = requests.post(
            f"{HOST_ADDRESS}/{VERSION}/conversation/completion",
            headers=_make_auth(scan_auth),
            json={
                "conversation_id": conv_id,
                "messages": [{"role": "user", "content": "胆囊"}],
                "stream": False,
            },
            timeout=120,
        )
        result = resp.json()
        print(f"  Chat: code={result.get('code')}, msg={result.get('message')}")

        if result.get("code") == 0:
            answer = result.get("data", {})
            reference = answer.get("reference", {})

            chunks = reference.get("chunks", [])
            doc_aggs = reference.get("doc_aggs", [])
            print(f"  Reference chunks: {len(chunks)}, doc_aggs: {len(doc_aggs)}")

            for c in chunks:
                did = c.get("doc_id", "")[:30]
                st = c.get("source_type")
                loc = c.get("location")
                print(f"    chunk: doc_id={did}..., source_type={st}, location={loc}")
                assert "source_type" in c, f"Chunk missing source_type! Keys: {list(c.keys())}"
                assert "location" in c, f"Chunk missing location! Keys: {list(c.keys())}"

            for d in doc_aggs:
                did = d.get("doc_id", "")[:30]
                st = d.get("source_type")
                loc = d.get("location")
                print(f"    doc_agg: doc_id={did}..., source_type={st}, location={loc}")
                assert "source_type" in d, f"doc_agg missing source_type! Keys: {list(d.keys())}"
                assert "location" in d, f"doc_agg missing location! Keys: {list(d.keys())}"

            print(f"  PASS: Chat reference has source_type and location on all chunks and doc_aggs")
        else:
            print(f"  Chat failed: {result.get('message')}")
