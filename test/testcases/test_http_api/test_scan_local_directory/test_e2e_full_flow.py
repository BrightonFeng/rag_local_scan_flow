#!/usr/bin/env python3
"""
End-to-end test for local scan file retrieval:
1. Create KB with /hdd1/test_scan/ scan path
2. Wait for parsing, verify 骑马.mp4 and 2014胆囊.jpg parsed
3. Test search for "胆囊照片"
4. Test chat with "胆囊照片"
"""

import sys
import time
import os
import requests

sys.path.insert(0, "/ragflow")

from common import settings

settings.init_settings()

# Hardcoded config values
HOST_ADDRESS = os.getenv("HOST_ADDRESS", "http://127.0.0.1:9380")
VERSION = "v1"
EMAIL = "qa@infiniflow.org"
PASSWORD = """ctAseGvejiaSWWZ88T/m4FQVOpQyUvP+x7sXtdv3feqZACiQleuewkUi35E16wSd5C5QcnkkcV9cYc8TKPTRZlxappDuirxghxoOvFcJxFU4ixLsD
fN33jCHRoDUW81IH9zjij/vaw8IbVyb6vuwg6MX6inOEBRRzVbRYxXOu1wkWY6SsI8X70oF9aeLFp/PzQpjoe/YbSqpTq8qqrmHzn9vO+yvyYyvmDsphXe
X8f7fp9c7vUsfOCkM+gHY3PadG+QHa7KI7mzTKgUTZImK6BZtfRBATDTthEUbbaTewY4H0MnWiCeeDhcbeQao6cFy1To8pE3RpmxnGnS8BsBn8w=="""

HOST = HOST_ADDRESS


def login():
    response = requests.post(f"{HOST}/{VERSION}/user/login", json={"email": EMAIL, "password": PASSWORD}, timeout=30)
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert data.get("code") == 0, f"Login error: {data}"
    return response.headers.get("Authorization")


def create_kb(auth, name, scan_path):
    """Create KB with local scan path."""
    resp = requests.post(
        f"{HOST}/{VERSION}/kb/create",
        headers={"Authorization": auth},
        json={
            "name": name,
            "embd_id": "qwen3-embedding:4b",
            "tenant_embd_id": 8,
        },
        timeout=30,
    )
    data = resp.json()
    print(f"Create KB: code={data.get('code')}")
    assert data.get("code") == 0, f"Create KB failed: {data}"
    kb_id = data["data"]["kb_id"]

    # Add scan path
    scan_resp = requests.post(f"{HOST}/{VERSION}/document/scan_path", headers={"Authorization": auth}, json={"kb_id": kb_id, "path": scan_path, "scan_interval": 10080}, timeout=30)
    scan_data = scan_resp.json()
    print(f"Scan path: code={scan_data.get('code')}, msg={scan_data.get('message')}")

    return kb_id


def wait_for_parsing(auth, kb_id, timeout=300):
    """Wait for documents to be parsed."""
    print("Waiting for parsing...")
    start = time.time()

    while time.time() - start < timeout:
        resp = requests.get(f"{HOST}/{VERSION}/document", headers={"Authorization": auth}, params={"kb_id": kb_id}, timeout=30)
        data = resp.json()

        if data.get("code") == 0 and data.get("data"):
            docs = data["data"]
            print(f"  Found {len(docs)} documents")

            # Check specific files
            horse_video = None
            gallbladder_jpg = None
            for doc in docs:
                if "骑马" in doc.get("name", ""):
                    horse_video = doc
                if "胆囊" in doc.get("name", "") and doc.get("name", "").endswith(".jpg"):
                    gallbladder_jpg = doc

            # Check if both are parsed (chunk_count > 0)
            parsed_count = sum(1 for d in docs if d.get("chunk_count", 0) > 0)
            print(f"  Parsed: {parsed_count}/{len(docs)}")

            if horse_video and gallbladder_jpg:
                horse_parsed = horse_video.get("chunk_count", 0) > 0
                gallbladder_parsed = gallbladder_jpg.get("chunk_count", 0) > 0

                # Verify content contains expected keywords
                if horse_parsed and gallbladder_parsed:
                    print(f"  骑马.mp4: chunk_count={horse_video.get('chunk_count')}")
                    print(f"  2014胆囊.jpg: chunk_count={gallbladder_jpg.get('chunk_count')}")

                    # Get chunks to verify content
                    chunk_resp = requests.get(f"{HOST}/{VERSION}/chunk/list", headers={"Authorization": auth}, params={"document_id": gallbladder_jpg["id"]}, timeout=30)
                    chunk_data = chunk_resp.json()
                    if chunk_data.get("code") == 0 and chunk_data.get("data"):
                        content = chunk_data["data"][0].get("content", "")
                        print(f"  2014胆囊.jpg content preview: {content[:100]}...")
                        assert "胆囊" in content, "胆囊 not in content!"

                    return True

        time.sleep(10)

    raise TimeoutError(f"Parsing timeout after {timeout}s")


def test_search(auth, kb_id):
    """Test search for '胆囊照片'."""
    print("\n=== Testing Search ===")

    # Create search session (conversation)
    conv_resp = requests.post(
        f"{HOST}/{VERSION}/conversation/set",
        headers={"Authorization": auth},
        json={
            "dialog_id": kb_id,  # Use KB as placeholder
            "name": "Search test",
        },
        timeout=30,
    )
    conv_data = conv_resp.json()
    print(f"Create search session: code={conv_data.get('code')}")

    # Use retrieval_test API to simulate search
    ret_resp = requests.post(
        f"{HOST}/{VERSION}/chunk/retrieval_test", headers={"Authorization": auth}, json={"kb_id": kb_id, "question": "胆囊照片", "page": 1, "size": 10, "highlight": True}, timeout=30
    )
    ret_data = ret_resp.json()
    print(f"Retrieval test: code={ret_data.get('code')}")

    if ret_data.get("code") == 0 and ret_data.get("data"):
        chunks = ret_data["data"].get("chunks", [])
        doc_aggs = ret_data["data"].get("doc_aggs", [])

        print(f"  Chunks: {len(chunks)}, Doc_aggs: {len(doc_aggs)}")

        for c in chunks:
            source_type = c.get("source_type")
            location = c.get("location")
            content = c.get("content", "")[:50]
            print(f"    chunk: source_type={source_type}, location={location}")
            print(f"      content: {content}...")

        for d in doc_aggs:
            source_type = d.get("source_type")
            location = d.get("location")
            doc_name = d.get("doc_name")
            print(f"    doc_agg: doc_name={doc_name}, source_type={source_type}, location={location}")

        # Verify enrichment
        assert len(doc_aggs) > 0, "No doc_aggs returned"

        gallbladder_agg = None
        for d in doc_aggs:
            if "胆囊" in d.get("doc_name", ""):
                gallbladder_agg = d
                break

        assert gallbladder_agg, "胆囊 file not in results"
        assert gallbladder_agg.get("source_type") == "local_scan", f"Wrong source_type: {gallbladder_agg.get('source_type')}"
        assert gallbladder_agg.get("location", "").endswith("2014胆囊.jpg"), f"Wrong location: {gallbladder_agg.get('location')}"

        print("  ✓ Search results enriched correctly!")
        return True
    else:
        print(f"  No retrieval data: {ret_data}")
        return False


def test_chat(auth, kb_id):
    """Test chat with '胆囊照片'."""
    print("\n=== Testing Chat ===")

    # Create dialog
    dialog_resp = requests.post(f"{HOST}/{VERSION}/dialog", headers={"Authorization": auth}, json={"name": "Chat test for 胆囊", "kb_ids": [kb_id], "llm_id": "qwen3.5:9b@Ollama"}, timeout=30)
    dialog_data = dialog_resp.json()
    print(f"Create dialog: code={dialog_data.get('code')}")

    if dialog_data.get("code") != 0:
        print(f"  Dialog creation failed: {dialog_data}")
        # Try to find existing dialog with this KB
        list_resp = requests.get(f"{HOST}/{VERSION}/dialog/list", headers={"Authorization": auth}, timeout=30)
        list_data = list_resp.json()
        if list_data.get("code") == 0:
            for d in list_data.get("data", []):
                if kb_id in d.get("kb_ids", []):
                    dialog_id = d["id"]
                    print(f"  Using existing dialog: {dialog_id}")
                    break
        else:
            print(f"  Could not list dialogs: {list_data}")
            return False
    else:
        dialog_id = dialog_data["data"]["id"]

    # Create conversation
    conv_resp = requests.post(f"{HOST}/{VERSION}/conversation/set", headers={"Authorization": auth}, json={"dialog_id": dialog_id, "name": "Chat test"}, timeout=30)
    conv_data = conv_resp.json()
    print(f"Create conversation: code={conv_data.get('code')}")

    if conv_data.get("code") != 0:
        print(f"  Conversation creation failed: {conv_data}")
        return False

    conv_id = conv_data["data"]["id"]

    # Send chat message
    chat_resp = requests.post(f"{HOST}/{VERSION}/conversation/completion", headers={"Authorization": auth}, json={"conversation_id": conv_id, "question": "胆囊照片", "stream": False}, timeout=120)
    chat_data = chat_resp.json()
    print(f"Chat completion: code={chat_data.get('code')}")

    if chat_data.get("code") != 0:
        print(f"  Chat failed: {chat_data}")
        return False

    # Check response for file links
    answer = chat_data.get("data", {}).get("answer", "")
    print(f"  Answer: {answer[:200]}...")

    # Check for references
    reference = chat_data.get("data", {}).get("reference", {})
    doc_aggs = reference.get("doc_aggs", [])
    chunks = reference.get("chunks", [])

    print(f"  References: doc_aggs={len(doc_aggs)}, chunks={len(chunks)}")

    for d in doc_aggs:
        source_type = d.get("source_type")
        location = d.get("location")
        doc_name = d.get("doc_name")
        print(f"    doc_agg: doc_name={doc_name}, source_type={source_type}, location={location}")

    # Verify enrichment
    gallbladder_ref = None
    for d in doc_aggs:
        if "胆囊" in d.get("doc_name", ""):
            gallbladder_ref = d
            break

    if gallbladder_ref:
        assert gallbladder_ref.get("source_type") == "local_scan", f"Wrong source_type: {gallbladder_ref.get('source_type')}"
        assert "2014胆囊.jpg" in gallbladder_ref.get("location", ""), f"Wrong location: {gallbladder_ref.get('location')}"
        print("  ✓ Chat references enriched correctly!")
        return True
    else:
        print("  Warning: 胆囊 file not in chat references")
        # Check if answer at least mentions it
        if "胆囊" in answer:
            print("  ✓ Chat answer contains 胆囊")
            return True
        return False


def main():
    print("=" * 60)
    print("E2E Test: Local Scan File Retrieval")
    print("=" * 60)

    auth = login()
    print(f"Logged in: {EMAIL}")

    # Step 1: Create KB with scan path
    kb_id = create_kb(auth, "E2E Test KB", "/hdd1/test_scan")
    print(f"Created KB: {kb_id}")

    # Step 2: Wait for parsing
    wait_for_parsing(auth, kb_id, timeout=300)

    # Step 3: Test search
    search_ok = test_search(auth, kb_id)

    # Step 4: Test chat
    chat_ok = test_chat(auth, kb_id)

    print("\n" + "=" * 60)
    print("RESULTS:")
    print(f"  Search: {'PASS' if search_ok else 'FAIL'}")
    print(f"  Chat: {'PASS' if chat_ok else 'FAIL'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
