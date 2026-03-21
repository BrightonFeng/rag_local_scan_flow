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
import shutil

import pytest
from configs import HOST_ADDRESS, VERSION


@pytest.fixture(scope="session", autouse=True)
def set_tenant_info():
    pass


HOST = HOST_ADDRESS
API_DOCUMENT_URL = f"{HOST}/{VERSION}/document"
API_SCAN_PATH_URL = f"{HOST}/{VERSION}/document/scan_path"
API_SCANNED_DIRS_URL = f"{HOST}/{VERSION}/document/scanned_directories"
API_RETRIEVAL_TEST_URL = f"{HOST}/{VERSION}/chunk/retrieval_test"
API_LLM_URL = f"{HOST}/{VERSION}/llm"

TEST_SCAN_DIR = "/hdd1/test_scan"
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
if os.path.exists("/.dockerenv") and OLLAMA_HOST == "http://localhost:11434":
    OLLAMA_HOST = "http://host.docker.internal:11434"


@pytest.fixture(scope="module")
def configure_ollama_img2txt(scan_auth):
    import requests

    tenant_url = f"{HOST}/{VERSION}/user/tenant_info"
    tenant_resp = requests.get(tenant_url, headers={"Authorization": scan_auth}, timeout=30)
    tenant_data = tenant_resp.json()
    if tenant_data.get("code") != 0:
        print(f"  [configure_ollama_img2txt] get tenant info failed: {tenant_data}")
        return

    tenant_id = tenant_data["data"].get("tenant_id")
    current = tenant_data["data"]

    llm_list_url = f"{HOST}/{VERSION}/llm/list"
    llm_resp = requests.get(llm_list_url, headers={"Authorization": scan_auth}, timeout=30)
    llm_data = llm_resp.json()
    if llm_data.get("code") != 0:
        print(f"  [configure_ollama_img2txt] list llm failed: {llm_data}")
        return

    ollama_factory = None
    for factory in llm_data.get("data", {}):
        if "Ollama" in factory:
            ollama_factory = factory
            break

    if not ollama_factory:
        print("  [configure_ollama_img2txt] no Ollama factory found")
        return

    img2txt_model = None
    for m in llm_data["data"].get(ollama_factory, []):
        if m.get("model_type") == "image2text":
            img2txt_model = m.get("llm_name")
            break

    if not img2txt_model:
        print("  [configure_ollama_img2txt] no Ollama image2text model found")
        return

    img2txt_id = f"{img2txt_model}@{ollama_factory}"
    print(f"  [configure_ollama_img2txt] setting img2txt_id={img2txt_id}")

    set_url = f"{HOST}/{VERSION}/user/set_tenant_info"
    set_resp = requests.post(
        set_url,
        headers={"Authorization": scan_auth},
        json={
            "tenant_id": tenant_id,
            "llm_id": current.get("llm_id", ""),
            "embd_id": current.get("embd_id", ""),
            "img2txt_id": img2txt_id,
            "asr_id": current.get("asr_id", ""),
            "tts_id": current.get("tts_id"),
        },
        timeout=30,
    )
    result = set_resp.json()
    if result.get("code") != 0:
        print(f"  [configure_ollama_img2txt] set failed: {result}")


@pytest.fixture(scope="session")
def scan_auth():
    import requests
    from configs import EMAIL, PASSWORD

    response = requests.post(f"{HOST}/{VERSION}/user/login", json={"email": EMAIL, "password": PASSWORD}, timeout=30)
    return response.headers.get("Authorization")


@pytest.fixture(scope="session")
def ollama_client():
    import ollama

    return ollama.Client(host=OLLAMA_HOST)


def _make_auth_param(auth):
    if hasattr(auth, "_token"):
        return auth
    return {"Authorization": str(auth)}


def scan_path(auth, kb_id, path, scan_interval=10080):
    r = pytest.importorskip("requests")
    resp = r.post(API_SCAN_PATH_URL, headers=_make_auth_param(auth), json={"kb_id": kb_id, "path": path, "scan_interval": scan_interval}, timeout=30)
    return resp.json()


def list_documents(auth, kb_id):
    r = pytest.importorskip("requests")
    resp = r.get(API_DOCUMENT_URL, headers=_make_auth_param(auth), params={"kb_id": kb_id}, timeout=30)
    return resp.json()


def get_scanned_directories(auth, kb_id):
    r = pytest.importorskip("requests")
    resp = r.get(API_SCANNED_DIRS_URL, headers=_make_auth_param(auth), params={"kb_id": kb_id}, timeout=30)
    return resp.json()


def update_scan_interval(auth, dir_id, scan_interval):
    r = pytest.importorskip("requests")
    resp = r.put(f"{API_SCANNED_DIRS_URL}/{dir_id}", headers=_make_auth_param(auth), json={"scan_interval": scan_interval}, timeout=30)
    return resp.json()


def retrieval_test(auth, kb_id, question, page=1, size=10):
    r = pytest.importorskip("requests")
    resp = r.post(API_RETRIEVAL_TEST_URL, headers=_make_auth_param(auth), json={"kb_id": kb_id, "question": question, "page": page, "size": size, "highlight": True}, timeout=30)
    return resp.json()


def setup_module(module):
    os.makedirs(TEST_SCAN_DIR, exist_ok=True)


def teardown_module(module):
    if os.path.exists(TEST_SCAN_DIR):
        for entry in os.listdir(TEST_SCAN_DIR):
            if entry.endswith(".mp4"):
                continue
            path = os.path.join(TEST_SCAN_DIR, entry)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
