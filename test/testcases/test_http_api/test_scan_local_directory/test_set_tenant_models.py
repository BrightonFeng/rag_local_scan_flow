import requests
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

# Get tenant info
print("Getting tenant info...")
response = requests.get(f"{HOST}/{VERSION}/user/tenant_info", headers=headers, timeout=30)
tenant = response.json()["data"]
print(f"Tenant: {tenant['name']}, ID: {tenant['tenant_id']}")

# First, let's get the model IDs
response = requests.get(f"{HOST}/{VERSION}/llm/list", headers=headers, timeout=30)
ollama_models = response.json()["data"].get("Ollama", [])

# Find the model IDs - convert to string
llm_id = None
embd_id = None
img2txt_id = None

for m in ollama_models:
    mid = str(m.get("id", ""))
    if m["model_type"] == "chat" and not llm_id:
        llm_id = mid
    elif m["model_type"] == "embedding" and not embd_id:
        embd_id = mid
    elif m["model_type"] == "image2text" and not img2txt_id:
        img2txt_id = mid

print(f"\nModel IDs: llm={llm_id}, embd={embd_id}, img2txt={img2txt_id}")

# Update tenant - need all required fields
print("\nUpdating tenant with model IDs...")
response = requests.post(
    f"{HOST}/{VERSION}/user/set_tenant_info", headers=headers, json={"tenant_id": tenant["tenant_id"], "llm_id": llm_id, "embd_id": embd_id, "img2txt_id": img2txt_id, "asr_id": ""}, timeout=30
)
print(f"Update response: {response.json()}")

# Verify
response = requests.get(f"{HOST}/{VERSION}/user/tenant_info", headers=headers, timeout=30)
tenant = response.json()["data"]
print(f"\nUpdated tenant models: llm_id={tenant['llm_id']}, embd_id={tenant['embd_id']}, img2txt_id={tenant['img2txt_id']}")
