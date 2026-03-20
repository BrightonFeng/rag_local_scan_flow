#!/usr/bin/env python3
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

import pytest
import requests
from configs import HOST_ADDRESS, VERSION

HOST = HOST_ADDRESS
OLLAMA_BASE_URL = "http://localhost:11434"


@pytest.mark.p1
class TestOllamaConfiguration:
    """Configure Ollama as LLM provider for the tenant."""

    def test_set_ollama_api_key(self, scan_auth):
        """Set Ollama API key (empty, since Ollama doesn't need one)."""
        response = requests.post(
            f"{HOST}/{VERSION}/llm/set_api_key",
            headers={"Authorization": str(scan_auth)},
            json={"llm_factory": "Ollama", "api_key": "", "base_url": OLLAMA_BASE_URL},
            timeout=60,
        )
        print(f"\n  {response.json()}")
        assert response.status_code == 200

    def test_list_ollama_models(self, scan_auth):
        """List available Ollama models."""
        response = requests.get(f"{HOST}/{VERSION}/llm/list", headers={"Authorization": str(scan_auth)}, timeout=30)
        data = response.json()["data"]
        assert "Ollama" in data, "Ollama factory not found"
        ollama_models = data["Ollama"]
        for m in ollama_models:
            print(f"  - {m['llm_name']} ({m['model_type']}) available={m.get('available')}")
        assert len(ollama_models) > 0, "No Ollama models found"

    def test_set_tenant_models_for_ollama(self, scan_auth):
        """Set tenant models to use Ollama for LLM, embedding, and image2text."""
        response = requests.get(f"{HOST}/{VERSION}/llm/list", headers={"Authorization": str(scan_auth)}, timeout=30)
        ollama_models = response.json()["data"].get("Ollama", [])

        llm_id = embd_id = img2txt_id = None
        for m in ollama_models:
            mid = str(m.get("id", ""))
            if m["model_type"] == "chat" and not llm_id:
                llm_id = mid
            elif m["model_type"] == "embedding" and not embd_id:
                embd_id = mid
            elif m["model_type"] == "image2text" and not img2txt_id:
                img2txt_id = mid

        response = requests.get(f"{HOST}/{VERSION}/user/tenant_info", headers={"Authorization": str(scan_auth)}, timeout=30)
        tenant = response.json()["data"]
        print(f"\n  Tenant: {tenant['name']}")

        response = requests.post(
            f"{HOST}/{VERSION}/user/set_tenant_info",
            headers={"Authorization": str(scan_auth)},
            json={"tenant_id": tenant["tenant_id"], "llm_id": llm_id, "embd_id": embd_id, "img2txt_id": img2txt_id, "asr_id": ""},
            timeout=30,
        )
        print(f"  Update response: {response.json()}")
        assert response.json().get("code") == 0
