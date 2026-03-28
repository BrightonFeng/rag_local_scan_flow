# local_scan 测试用例

## 测试目录结构

```
test/testcases/test_http_api/test_scan_local_directory/
├── conftest.py                      # 共享 fixtures 和辅助函数
├── video_utils.py                   # 视频帧提取工具
├── test_scan_path.py                # 扫描路径基础功能测试
├── test_ollama_setup.py             # Ollama LLM 配置测试
├── test_local_scan_full_flow.py     # local_scan 完整流程测试（搜索+聊天）
├── test_video_ollama.py             # Ollama VLM 视频帧解析测试
└── test_ui_automation.py           # UI 自动化测试（Playwright）
```

## 快速运行

```bash
# 运行所有测试 (p2 级别)
cd /home/bf/ragflow/test/testcases
PYTHONPATH=/home/bf/ragflow/test/testcases pytest test_http_api/test_scan_local_directory/ -v

# 运行快速测试 (~5秒)
PYTHONPATH=/home/bf/ragflow/test/testcases pytest test_http_api/test_scan_local_directory/test_scan_path.py -v
PYTHONPATH=/home/bf/ragflow/test/testcases pytest test_http_api/test_scan_local_directory/test_ollama_setup.py -v

# 运行完整流程测试 (~6分钟)
PYTHONPATH=/home/bf/ragflow/test/testcases pytest test_http_api/test_scan_local_directory/test_local_scan_full_flow.py -v -s
```

## 依赖条件

### 环境依赖
| 依赖 | 说明 |
|---|---|
| RAGFlow API | `http://127.0.0.1:9380` |
| Ollama 服务 | `http://localhost:11434`（需包含 `qwen3-vl:8b` 和 `qwen3-embedding:4b` 模型） |
| 测试文件 | `/hdd1/test_scan/` 目录下的测试文件 |

### 测试文件
测试使用 `/hdd1/test_scan/` 目录下的文件：

| 文件路径 | 内容描述 |
|---|---|
| `/hdd1/test_scan/091125.mp4` | 树袋熊（koala） |
| `/hdd1/test_scan/100305.mp4` | 蜥蜴（lizard） |
| `/hdd1/test_scan/海狮1.mp4` | 海狮（sea lion） |
| `/hdd1/test_scan/骑马.mp4` | 骑马（horse） |
| `/hdd1/test_scan/2014胆囊.jpg` | 胆囊超声检查图片 |

---

## 测试用例说明

### test_scan_path.py
- `test_scan_path_without_auth` - 无认证扫描应失败
- `test_scan_path_invalid_path` - 无效路径扫描应失败

### test_ollama_setup.py
- `test_set_ollama_api_key` - 配置 Ollama API key
- `test_list_ollama_models` - 列出 Ollama 模型
- `test_set_tenant_models_for_ollama` - 设置租户使用 Ollama

### test_local_scan_full_flow.py
完整流程测试（E2E）：
1. 创建 KB 并扫描 `/hdd1/test_scan/`
2. 等待文档解析完成（验证 chunk_num > 0）
3. 验证 Search API 返回 `source_type` + `location`
4. 验证 Chat API 返回 enrichment 字段

### test_video_ollama.py
- 参数化测试：Ollama VLM 解析视频帧
- 4 个视频 × 2 种测试（单次运行 + 稳定性测试）

### test_ui_automation.py
- Playwright UI 自动化测试

---

## Enrichment 功能说明

### 功能描述
local_scan 文件在检索和聊天时需要返回 `source_type` 和 `location` 字段。

### API 响应格式
```json
{
  "data": {
    "doc_aggs": [
      {
        "doc_id": "xxx",
        "doc_name": "2014胆囊.jpg",
        "source_type": "local_scan",
        "location": "/hdd1/test_scan/2014胆囊.jpg"
      }
    ],
    "chunks": [
      {
        "doc_id": "xxx",
        "source_type": "local_scan",
        "location": "/hdd1/test_scan/2014胆囊.jpg"
      }
    ]
  }
}
```

---

## 共享 Fixtures（conftest.py）

| Fixture | Scope | 说明 |
|---|---|---|
| `scan_auth` | session | 登录获取 Authorization header |
| `ollama_client` | session | Ollama Python 客户端 |
| `configure_ollama_img2txt` | module | 自动配置 Ollama image2text 模型 |

### 共享辅助函数

| 函数 | 说明 |
|---|---|
| `scan_path(auth, kb_id, path, scan_interval)` | POST `/v1/document/scan_path` |
| `list_documents(auth, kb_id)` | GET `/v1/document` |
| `retrieval_test(auth, kb_id, question, ...)` | POST `/v1/chunk/retrieval_test` |

---

## 已知限制

1. 测试文件路径 `/hdd1/test_scan/` 必须在服务器上存在
2. 聊天测试需要 Ollama embedding 模型可用
3. 稳定性测试（5 次）耗时约 65 秒/视频
