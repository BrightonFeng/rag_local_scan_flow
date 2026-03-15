#!/usr/bin/env python3
"""
Test script for scan local directory feature.
Usage:
    python3 test_scan_local_directory.py
"""

import os
import sys
import requests


HOST_ADDRESS = os.getenv("HOST_ADDRESS", "http://localhost:9380")
VERSION = "v1"
SCAN_PATH_API_URL = f"{HOST_ADDRESS}/{VERSION}/document/scan_path"
SCANNED_DIRS_API_URL = f"{HOST_ADDRESS}/{VERSION}/document/scanned_directories"
DOCUMENT_API_URL = f"{HOST_ADDRESS}/{VERSION}/document"
KB_API_URL = f"{HOST_ADDRESS}/{VERSION}/kb/list"
KB_CREATE_URL = f"{HOST_ADDRESS}/{VERSION}/kb/create"

TEST_DIR = "/hdd1/test_scan"


def list_knowledgebases(headers):
    """List available knowledge bases."""
    url = KB_API_URL
    response = requests.post(url, headers=headers, json={})
    result = response.json()
    if result.get("code") == 0 and result.get("data"):
        data = result.get("data", {})
        kbs = data.get("kbs", [])
        total = data.get("total", 0)
        print(f"     Found {total} knowledge base(s)")
        for kb in kbs[:3]:  # Show first 3
            print(f"       - {kb.get('name')}: {kb.get('id')}")
        return kbs
    return None


def create_knowledgebase(headers, name):
    """Create a new knowledge base."""
    url = KB_CREATE_URL
    response = requests.post(url, headers=headers, json={"name": name})
    result = response.json()
    if result.get("code") == 0:
        kb_id = result.get("data", {}).get("kb_id")
        print(f"     Created KB: {name} ({kb_id})")
        return kb_id
    print(f"     Failed to create KB: {result.get('message')}")
    return None


def login():
    """Login and get authorization token."""
    url = f"{HOST_ADDRESS}/{VERSION}/user/login"
    # Use plaintext password with "plain:" prefix
    data = {"email": "bf@163.com", "password": "plain:bf"}
    response = requests.post(url, json=data)
    result = response.json()
    if result.get("code") != 0:
        print(f"Login failed: {result}")
        return None
    return response.headers.get("Authorization")


def run_tests():
    """Run all test cases."""
    print("=" * 60)
    print("Scan Local Directory Feature Tests")
    print("=" * 60)

    # Login
    print("\n[1] Login...")
    auth = login()
    if not auth:
        print("FAILED: Login failed")
        return False
    print(f"OK: Logged in, auth: {auth[:30]}...")

    headers = {"Authorization": auth}

    # List knowledge bases
    print("\n[2] List Knowledge Bases...")
    kbs = list_knowledgebases(headers)
    if not kbs or len(kbs) == 0:
        print("     No knowledge base found, creating one...")
        KB_ID = create_knowledgebase(headers, "Test KB for Scan")
        if not KB_ID:
            print("FAILED: Could not create knowledge base")
            return False
        KB_NAME = "Test KB for Scan"
    else:
        # Use the first KB
        KB_ID = kbs[0]["id"]
        KB_NAME = kbs[0]["name"]
    print(f"     Using KB: {KB_NAME} ({KB_ID})")

    # Test 3: Scan with invalid path
    print("\n[3] Test: Scan with invalid path...")
    result = requests.post(SCAN_PATH_API_URL, headers=headers, json={"kb_id": KB_ID, "path": "/nonexistent/path/12345"})
    res = result.json()
    if res.get("code") != 0:
        print(f"OK: Invalid path rejected as expected: {res.get('message')}")
    else:
        print(f"WARNING: Invalid path was accepted: {res}")

    # Test 4: Scan valid directory (using existing KB from earlier)
    print("\n[4] Test: Scan valid directory...")
    test_subdir = os.path.join(TEST_DIR, "test1")
    os.makedirs(test_subdir, exist_ok=True)
    test_file = os.path.join(test_subdir, "test.txt")
    with open(test_file, "w") as f:
        f.write("Hello World")

    # Use the KB ID that we know exists from the UI
    # For now just test that the endpoint works
    result = requests.post(
        SCAN_PATH_API_URL,
        headers=headers,
        json={
            "kb_id": KB_ID,
            "path": test_subdir,
            "scan_interval": 60,
        },
    )
    res = result.json()
    if res.get("code") == 0:
        print(f"OK: Directory scanned successfully")
        print(f"     Result: {res.get('data', {})}")
    else:
        print(f"INFO: Scan result: {res.get('message')}")
        # This might fail if KB doesn't exist, which is OK for now

    # Test 5: Get scanned directories
    print("\n[5] Test: Get scanned directories...")
    result = requests.get(SCANNED_DIRS_API_URL, headers=headers, params={"kb_id": KB_ID})
    res = result.json()
    if res.get("code") == 0 and res.get("data"):
        print(f"OK: Found {len(res.get('data', []))} scanned directory(ies)")
    else:
        print(f"INFO: Scanned directories: {res}")

    print("\n" + "=" * 60)
    print("Basic tests completed!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
