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


HOST = HOST_ADDRESS
API_DOCUMENT_URL = f"{HOST}/{VERSION}/document"
API_SCAN_PATH_URL = f"{HOST}/{VERSION}/document/scan_path"
API_SCANNED_DIRS_URL = f"{HOST}/{VERSION}/document/scanned_directories"
API_RETRIEVAL_TEST_URL = f"{HOST}/{VERSION}/chunk/retrieval_test"
API_LLM_URL = f"{HOST}/{VERSION}/llm"

TEST_SCAN_DIR = "/hdd1/test_scan"
OLLAMA_HOST = "http://localhost:11434"


@pytest.fixture(scope="session", autouse=True)
def set_tenant_info():
    pass


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
    resp = r.post(API_SCAN_PATH_URL, auth=_make_auth_param(auth), json={"kb_id": kb_id, "path": path, "scan_interval": scan_interval}, timeout=30)
    return resp.json()


def list_documents(auth, kb_id):
    r = pytest.importorskip("requests")
    resp = r.get(API_DOCUMENT_URL, auth=_make_auth_param(auth), params={"kb_id": kb_id}, timeout=30)
    return resp.json()


def get_scanned_directories(auth, kb_id):
    r = pytest.importorskip("requests")
    resp = r.get(API_SCANNED_DIRS_URL, auth=_make_auth_param(auth), params={"kb_id": kb_id}, timeout=30)
    return resp.json()


def update_scan_interval(auth, dir_id, scan_interval):
    r = pytest.importorskip("requests")
    resp = r.put(f"{API_SCANNED_DIRS_URL}/{dir_id}", auth=_make_auth_param(auth), json={"scan_interval": scan_interval}, timeout=30)
    return resp.json()


def retrieval_test(auth, kb_id, question, page=1, size=10):
    r = pytest.importorskip("requests")
    resp = r.post(API_RETRIEVAL_TEST_URL, auth=_make_auth_param(auth), json={"kb_id": kb_id, "question": question, "page": page, "size": size, "highlight": True}, timeout=30)
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
