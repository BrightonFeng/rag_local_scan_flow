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


@pytest.mark.p1
class TestScanLocalDirectory:
    """Test cases for scan local directory feature."""

    def test_scan_path_without_auth(self):
        """Test scanning without authentication should fail."""
        res = pytest.importorskip("requests").post(
            f"{pytest.importorskip('configs').HOST_ADDRESS}/v1/document/scan_path",
            json={"kb_id": "kb_id", "path": "/tmp/test"},
        )
        assert res.json()["code"] != 0

    def test_scan_path_invalid_path(self, scan_auth):
        """Test scanning with invalid path should fail."""
        import requests
        from configs import HOST_ADDRESS, VERSION

        kb_resp = requests.post(
            f"{HOST_ADDRESS}/{VERSION}/kb/create",
            headers={"Authorization": scan_auth},
            json={"name": "temp-kb-invalid-path"},
            timeout=30,
        )
        kb_data = kb_resp.json()
        assert kb_data.get("code") == 0, f"Failed to create KB: {kb_data}"
        kb_id = kb_data["data"]["kb_id"]

        from conftest import scan_path

        res = scan_path(scan_auth, kb_id, "/nonexistent/path/12345")
        assert res["code"] != 0

        requests.delete(
            f"{HOST_ADDRESS}/{VERSION}/kb/{kb_id}",
            headers={"Authorization": scan_auth},
            timeout=30,
        )
