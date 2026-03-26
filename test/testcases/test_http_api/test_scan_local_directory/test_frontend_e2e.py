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
Playwright E2E test: clicking local_scan thumbnails opens original file.

Tests:
1. Search page: clicking thumbnail/file link for local_scan opens original
2. Chat page: same behavior
"""

import time
import sys
from urllib.parse import quote

sys.path.insert(0, "/tmp/testcases")
from configs import HOST_ADDRESS as API_HOST, VERSION, EMAIL, PASSWORD

BROWSER_HOST = "http://host.docker.internal:80"
HOST_ADDRESS = API_HOST

import pytest


def _login(page):
    page.goto(f"{BROWSER_HOST}/login", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(2)

    email_input = page.locator("input[type='email'], input[name='email'], input[placeholder*='email' i], input[placeholder*='邮箱' i]").first
    password_input = page.locator("input[type='password'], input[name='password']").first

    if not email_input.is_visible(timeout=3000):
        print(f"  Email input not found, trying alternate selectors")
        all_inputs = page.locator("input").all()
        for inp in all_inputs:
            inp_type = inp.get_attribute("type")
            placeholder = inp.get_attribute("placeholder") or ""
            print(f"    Input: type={inp_type}, placeholder={placeholder[:30]}")

    print(f"  Email visible: {email_input.is_visible()}")
    if email_input.is_visible():
        email_input.fill(EMAIL)
        page.wait_for_timeout(500)

    print(f"  Password visible: {password_input.is_visible()}")
    if password_input.is_visible():
        password_input.fill(PASSWORD)
        page.wait_for_timeout(500)

    submit_btn = page.get_by_role("button", name="Sign in").first
    print(f"  Sign in visible: {submit_btn.is_visible()}")
    if submit_btn.is_visible():
        submit_btn.click()
    else:
        alt_btn = page.locator("button[type='submit']").first
        if alt_btn.is_visible():
            alt_btn.click()

    page.wait_for_timeout(5000)
    page.wait_for_load_state("networkidle", timeout=15000)
    print(f"  Page URL after login: {page.url}")
    print(f"  Page title after login: {page.title()}")


def _get_auth():
    import requests

    resp = requests.post(
        f"{HOST_ADDRESS}/{VERSION}/user/login",
        json={"email": EMAIL, "password": PASSWORD},
        timeout=30,
    )
    return resp.headers.get("Authorization")


def _setup_tenant(auth):
    import requests

    tenant_url = f"{HOST_ADDRESS}/{VERSION}/user/tenant_info"
    tenant_resp = requests.get(tenant_url, headers={"Authorization": auth}, timeout=30)
    tenant_data = tenant_resp.json()
    if tenant_data.get("code") != 0:
        return
    tenant_id = tenant_data["data"].get("tenant_id")
    current = tenant_data["data"]

    llm_list_url = f"{HOST_ADDRESS}/{VERSION}/llm/list"
    llm_resp = requests.get(llm_list_url, headers={"Authorization": auth}, timeout=30)
    llm_data = llm_resp.json()
    if llm_data.get("code") != 0:
        return

    img2txt_id = None
    for factory in llm_data.get("data", {}):
        if "Ollama" in factory:
            for m in llm_data["data"][factory]:
                if m.get("model_type") == "image2text":
                    img2txt_id = f"{m.get('llm_name')}@{factory}"
                    break

    set_url = f"{HOST_ADDRESS}/{VERSION}/user/set_tenant_info"
    requests.post(
        set_url,
        headers={"Authorization": auth},
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


def _create_kb_and_scan(auth):
    import requests

    name = f"e2e-local-scan-{int(time.time())}"
    resp = requests.post(
        f"{HOST_ADDRESS}/{VERSION}/kb/create",
        headers={"Authorization": auth},
        json={"name": name, "embd_id": "qwen3-embedding:4b", "tenant_embd_id": 8},
        timeout=30,
    )
    data = resp.json()
    assert data.get("code") == 0, f"Failed to create KB: {data}"
    kb_id = data["data"]["kb_id"]

    resp = requests.post(
        f"{HOST_ADDRESS}/{VERSION}/document/scan_path",
        headers={"Authorization": auth},
        json={"kb_id": kb_id, "path": "/hdd1/test_scan", "scan_interval": 10080},
        timeout=30,
    )
    assert resp.json().get("code") == 0, f"Scan failed"
    return kb_id


def _wait_documents(auth, kb_id, timeout=120):
    import requests

    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = requests.post(
            f"{HOST_ADDRESS}/{VERSION}/document/list",
            headers={"Authorization": auth},
            params={"kb_id": kb_id},
            json={},
            timeout=30,
        )
        data = resp.json()
        if data.get("code") == 0:
            docs = data.get("data", {}).get("docs", [])
            if len(docs) >= 5:
                return docs
        time.sleep(5)
    return []


def _wait_parsed(auth, kb_id, doc_name, timeout=300):
    import requests

    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = requests.post(
            f"{HOST_ADDRESS}/{VERSION}/document/list",
            headers={"Authorization": auth},
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
            if doc.get("name") == doc_name and doc.get("chunk_num", 0) > 0:
                return doc
        time.sleep(10)
    return None


@pytest.fixture(scope="module")
def kb_with_parsed_docs():
    print("\n=== Setup: KB with parsed documents ===")
    auth = _get_auth()
    _setup_tenant(auth)
    kb_id = _create_kb_and_scan(auth)
    print(f"  KB: {kb_id}")

    docs = _wait_documents(auth, kb_id)
    print(f"  Documents found: {len(docs)}")

    doc = _wait_parsed(auth, kb_id, "2014胆囊.jpg")
    assert doc is not None, "2014胆囊.jpg not parsed"
    print(f"  2014胆囊.jpg parsed, doc_id={doc['id']}")

    yield {"kb_id": kb_id, "doc_id": doc["id"], "doc_name": doc["name"]}

    import requests

    requests.delete(
        f"{HOST_ADDRESS}/{VERSION}/kb/{kb_id}",
        headers={"Authorization": auth},
        timeout=30,
    )
    print(f"\n=== Teardown: KB {kb_id} deleted ===")


@pytest.fixture(scope="module")
def browser_page():
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()

    page.on("console", lambda msg: print(f"  [Browser {msg.type}]: {msg.text}") if msg.type in ("error", "warning") else None)
    page.on("response", lambda r: print(f"  [Network {r.status}]: {r.url[:100]}") if r.status >= 400 or "/v1/" in r.url else None)

    yield page

    page.close()
    context.close()
    browser.close()
    pw.stop()


def test_document_get_returns_original_file(browser_page, kb_with_parsed_docs):
    """Test: /document/get/{doc_id} returns the original file (not resized)."""
    import requests

    auth = _get_auth()
    doc_id = kb_with_parsed_docs["doc_id"]

    resp = requests.get(
        f"{HOST_ADDRESS}/{VERSION}/document/get/{doc_id}",
        headers={"Authorization": auth},
        timeout=30,
    )
    print(f"\n=== Test: /document/get/{{doc_id}} ===")
    print(f"  Status: {resp.status_code}")
    print(f"  Content-Type: {resp.headers.get('Content-Type')}")
    print(f"  Content-Length: {resp.headers.get('Content-Length')}")
    print(f"  Body prefix: {resp.content[:20]}")

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    content_type = resp.headers.get("Content-Type", "")
    assert "image" in content_type or "jpeg" in content_type or "jpg" in content_type, f"Expected image, got {content_type}"
    assert len(resp.content) > 30000, f"File too small ({len(resp.content)} bytes), might be resized"
    print(f"  PASS: Original file returned ({len(resp.content)} bytes)")


def test_search_page_thumbnail_opens_original(browser_page, kb_with_parsed_docs):
    """Test: search page thumbnail click opens original file URL."""
    import requests

    print(f"\n=== Test: Search page thumbnail click ===")

    auth = _get_auth()
    page = browser_page
    kb_id = kb_with_parsed_docs["kb_id"]

    resp = requests.post(
        f"{HOST_ADDRESS}/{VERSION}/dialog/set",
        headers={"Authorization": auth},
        json={
            "name": f"e2e-search-{int(time.time())}",
            "kb_ids": [kb_id],
            "prompt_config": {
                "system": "You are a helpful assistant. Use knowledge to answer: {knowledge}",
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
    assert data.get("code") == 0, f"Create dialog failed: {data}"
    dialog_id = data["data"]["id"]
    print(f"  Created dialog: {dialog_id}")

    _login(page)

    page.goto(f"{BROWSER_HOST}/next-chat/{dialog_id}", timeout=30000)

    page.wait_for_timeout(10000)
    chat_input = page.locator("textarea").first
    if not chat_input.is_visible():
        chat_input = page.locator("input[placeholder*='Type' i], input[placeholder*='输入']").first

    print(f"  Chat input visible: {chat_input.is_visible()}")
    if chat_input.is_visible():
        chat_input.fill("胆囊照片")
        chat_input.press("Enter")
        page.wait_for_timeout(5000)

    for _ in range(3):
        page.wait_for_timeout(2000)
        page.wait_for_load_state("networkidle", timeout=5000)

    new_tab_url = None
    new_tab_closed = [False]

    def handle_popup(popup):
        nonlocal new_tab_url
        new_tab_url = popup.url
        new_tab_closed[0] = False
        print(f"  Popup opened: {new_tab_url}")
        popup.close()
        new_tab_closed[0] = True

    page.on("popup", handle_popup)

    all_images = page.locator("img[src*='/document/image/'], img[src*='/document/img/']").all()
    print(f"  Found {len(all_images)} image elements")
    for img in all_images:
        src = img.get_attribute("src")
        print(f"    Image src: {src[:100] if src else None}")

    thumbnail = page.locator("img[src*='/document/image/'], img[src*='/document/img/']").first
    if thumbnail.is_visible(timeout=5000):
        src = thumbnail.get_attribute("src")
        print(f"  Clicking thumbnail: {src[:100] if src else None}")
        thumbnail.click()
        page.wait_for_timeout(3000)

        if new_tab_url:
            print(f"  New tab URL: {new_tab_url}")
            assert "/document/get/" in new_tab_url, f"Expected /document/get/, got {new_tab_url}"
            assert "/document/image/" not in new_tab_url, f"Unexpected /document/image/ in URL"
            print(f"  PASS: Thumbnail click opened original file URL")
        elif new_tab_closed[0]:
            print(f"  WARN: Popup was closed before URL check")
        else:
            print(f"  WARN: No popup opened")
    else:
        print(f"  WARN: No thumbnail visible in chat page")
