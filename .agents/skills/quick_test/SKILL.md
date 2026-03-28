---
name: quick_test
description: Run 1 minutes quick tests for local directory scanning. Use this skill to verify core functionality without waiting for long-running tests.
---

Run the following tests in `test/testcases/test_http_api/test_scan_local_directory/`:

```bash
cd /home/bf/ragflow/test/testcases
PYTHONPATH=/home/bf/ragflow/test/testcases pytest test_http_api/test_scan_local_directory/test_scan_path.py test_http_api/test_scan_local_directory/test_ollama_setup.py -v
```

Expected: All tests should pass (~5 seconds)
