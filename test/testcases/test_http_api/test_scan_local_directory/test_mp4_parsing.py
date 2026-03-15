import requests
import time
import json

HOST = "http://127.0.0.1:9380"
VERSION = "v1"


def login():
    password = """ctAseGvejiaSWWZ88T/m4FQVOpQyUvP+x7sXtdv3feqZACiQleuewkUi35E16wSd5C5QcnkkcV9cYc8TKPTRZlxappDuirxghxoOvFcJxFU4ixLsD
fN33jCHRoDUW81IH9zjij/vaw8IbVyb6vuwg6MX6inOEBRRzVbRYxXOu1wkWY6SsI8X70oF9aeLFp/PzQpjoe/YbSqpTq8qqrmHzn9vO+yvyYyvmDsphXe
X8f7fp9c7vUsfOCkM+gHY3PadG+QHa7KI7mzTKgUTZImK6BZtfRBATDTthEUbbaTewY4H0MnWiCeeDhcbeQao6cFy1To8pE3RpmxnGnS8BsBn8w=="""
    response = requests.post(f"{HOST}/{VERSION}/user/login", json={"email": "qa@infiniflow.org", "password": password}, timeout=30)
    return response.headers.get("Authorization")


token = login()
headers = {"Authorization": str(token)}

# Create KB
print("Creating KB...")
response = requests.post(f"{HOST}/{VERSION}/kb/create", headers=headers, json={"name": f"test_mp4_{int(time.time())}"}, timeout=30)
kb_data = response.json()
if kb_data.get("code") != 0:
    print(f"Failed to create KB: {kb_data}")
    exit(1)
kb_id = kb_data["data"]["kb_id"]
print(f"Created KB: {kb_id}")

# Scan directory
test_dir = "/hdd1/test_scan/test1"
print(f"\nScanning {test_dir}...")
response = requests.post(f"{HOST}/{VERSION}/document/scan_path", headers=headers, json={"kb_id": kb_id, "path": test_dir, "scan_interval": 60}, timeout=30)
scan_result = response.json()
print(f"Scan result: {scan_result}")

if scan_result.get("code") != 0:
    print("Scan failed!")
    exit(1)

# Wait and check parsing status
print("\nWaiting for parsing...")
for i in range(12):  # 2 minutes
    time.sleep(10)
    response = requests.post(f"{HOST}/{VERSION}/document/list", headers=headers, params={"kb_id": kb_id}, timeout=30)
    docs = response.json()

    if docs.get("code") == 0 and docs.get("data"):
        for doc in docs["data"].get("docs", []):
            status = doc.get("status")
            chunk_num = doc.get("chunk_num")
            name = doc.get("name")
            print(f"  [{i * 10}s] {name}: status={status}, chunks={chunk_num}")

            if status == "failed":
                print(f"  FAILED! Checking details...")
                response = requests.get(f"{HOST}/{VERSION}/document/get/{doc['id']}", headers=headers, timeout=30)
                detail = response.json()
                print(f"  Detail: {json.dumps(detail, indent=2, ensure_ascii=False)[:500]}")
