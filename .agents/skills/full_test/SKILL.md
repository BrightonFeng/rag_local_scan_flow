---
name: full_test
description: Run all tests(10 minutes) in the test_scan_local_directory directory. Use this for comprehensive testing including full flow tests that may take 10+ minutes.
---

Run all tests in `test/testcases/test_http_api/test_scan_local_directory/`:

```bash
cd /home/bf/ragflow/test/testcases
PYTHONPATH=/home/bf/ragflow/test/testcases pytest test_http_api/test_scan_local_directory/ -v
```

Note: Full tests include:
- Quick tests (~5 seconds): test_scan_path.py, test_ollama_setup.py
- Long tests (~6 minutes): test_local_scan_full_flow.py (4 steps)
- Very long tests: test_video_ollama.py (8 parametrized tests with VLM)

Total time: ~10-15 minutes depending on video parsing speed.
