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

# First, set the API key for Ollama (empty, since Ollama doesn't need one)
print("Setting Ollama API key...")
response = requests.post(f"{HOST}/{VERSION}/llm/set_api_key", headers=headers, json={"llm_factory": "Ollama", "api_key": "", "base_url": "http://host.docker.internal:11434"}, timeout=60)
print(f"Set API key response: {response.json()}")

# Now check available models
print("\nChecking available models...")
response = requests.get(f"{HOST}/{VERSION}/llm/list", headers=headers, timeout=30)
data = response.json()["data"]
print(f"Available factories: {list(data.keys())}")
if "Ollama" in data:
    print("Ollama models:")
    for m in data["Ollama"]:
        print(f"  - {m['llm_name']} ({m['model_type']}) - available: {m.get('available')}")
