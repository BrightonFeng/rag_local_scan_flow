# local_scan 测试用例说明

## 测试目录

```
test/testcases/test_http_api/test_scan_local_directory/
├── conftest.py                      # 共享 fixtures 和辅助函数
├── video_utils.py                   # 视频帧提取工具和测试数据定义
├── test_scan_path.py                # 扫描路径基础功能测试
├── test_ollama_setup.py             # Ollama LLM 配置测试
├── test_mp4_parsing.py             # MP4 视频端到端解析测试
├── test_video_ollama.py             # Ollama VLM 视频帧解析测试
├── test_video_chunk.py              # rag.app.picture.chunk 视频解析测试
├── test_local_scan_full_flow.py     # local_scan 完整流程测试（搜索+聊天）
├── test_enrichment_integration.py   # enrichment 集成测试
├── test_enrichment_unit.py         # enrichment 单元测试
└── test_retrieval_source_type.py    # 检索结果 source_type 测试
```

## 快速运行

```bash
# 运行所有测试
pytest test/testcases/test_http_api/test_scan_local_directory/ -v

# 运行指定测试文件
pytest test/testcases/test_http_api/test_scan_local_directory/test_ollama_setup.py -v

# 运行单个测试
pytest "test/testcases/test_http_api/test_scan_local_directory/test_local_scan_full_flow.py" -v -s
```

## 依赖条件

### 环境依赖
| 依赖 | 说明 |
|---|---|
| RAGFlow API | `http://127.0.0.1:9380` 或 `http://localhost` |
| Ollama 服务 | `http://localhost:11434`（需包含 `qwen3-vl:8b` 和 `qwen3-embedding:4b` 模型） |
| 测试文件 | `/hdd1/test_scan/` 目录下的测试文件 |
| LLM Provider | Ollama（本地部署） |

### 测试文件
测试使用 `/hdd1/test_scan/` 目录下的文件：

| 文件路径 | 内容描述 |
|---|---|
| `/hdd1/test_scan/091125.mp4` | 树袋熊（koala） |
| `/hdd1/test_scan/100305.mp4` | 蜥蜴（lizard） |
| `/hdd1/test_scan/海狮1.mp4` | 海狮（sea lion） |
| `/hdd1/test_scan/骑马.mp4` | 骑马（horse） |
| `/hdd1/test_scan/2014胆囊.jpg` | 胆囊超声检查图片 |

### Python 依赖
| 包 | 说明 |
|---|---|
| pytest | 测试框架 |
| requests | HTTP 调用 |
| ollama | Ollama API 客户端 |
| opencv-python-headless | 视频帧提取 |

---

## 测试用例详解

### 1. test_scan_path.py — 扫描路径基础功能

#### `test_scan_path_without_auth`
- **功能**: 验证未认证请求扫描路径会被拒绝
- **方法**: 不带任何认证直接 POST `/v1/document/scan_path`
- **预期**: HTTP 返回非 0 code
- **依赖**: 无（不依赖认证）
- **运行时间**: < 1 秒

#### `test_scan_path_invalid_path`
- **功能**: 验证扫描不存在的路径会返回错误
- **方法**: 用认证调用 `/v1/document/scan_path`，路径为 `/nonexistent/path/12345`
- **预期**: 返回非 0 code
- **依赖**: `scan_auth` fixture

---

### 2. test_ollama_setup.py — Ollama LLM 配置

#### `test_set_ollama_api_key`
- **功能**: 配置 Ollama 作为 LLM Provider
- **方法**: POST `/v1/llm/set_api_key`，api_key 为空
- **预期**: HTTP 200
- **依赖**: `scan_auth` fixture

#### `test_list_ollama_models`
- **功能**: 验证 Ollama 模型列表可正确获取
- **方法**: GET `/v1/llm/list`
- **预期**: 返回数据中包含 "Ollama" factory

#### `test_set_tenant_models_for_ollama`
- **功能**: 将租户的 LLM / Embedding / Image2Text 模型切换为 Ollama
- **方法**: 获取 Ollama 模型列表 → 获取租户信息 → POST `/v1/user/set_tenant_info`
- **预期**: 设置成功，返回 code 0
- **依赖**: Ollama 服务必须运行并包含 chat/embedding/image2text 模型

---

### 3. test_mp4_parsing.py — MP4 端到端解析

#### `test_scan_video_directory_and_wait`
- **功能**: 创建知识库 → 扫描视频目录 → 等待解析完成 → 验证状态
- **方法**:
  1. POST `/v1/kb/create` 创建临时 KB
  2. POST `/v1/document/scan_path` 扫描 `/hdd1/test_scan`
  3. 轮询（最多 120 秒）检查文档解析状态
  4. 清理：DELETE `/v1/kb/{kb_id}`
- **预期**: 所有文档状态为 `success`
- **依赖**: Ollama 正常运行；视频文件存在

---

### 4. test_local_scan_full_flow.py — local_scan 完整流程测试

#### `TestLocalScanRetrievalFlow`
- **功能**: 端到端测试 local_scan 检索流程
- **测试步骤**:
  1. 创建 KB 并扫描 `/hdd1/test_scan/` 路径
  2. 等待文档解析完成
  3. 验证 "骑马.mp4" 解析结果包含"骑马"字样
  4. 验证 "2014胆囊.jpg" 解析结果包含"胆囊"字样
  5. 在搜索页面检索 "胆囊照片"，验证返回缩略图和文件链接
  6. 在聊天页面提问 "胆囊照片"，验证返回文件链接
- **关键验证点**:
  - `retrieval_test` 返回的 `doc_aggs` 和 `chunks` 包含 `source_type` 和 `location` 字段
  - 聊天 references 包含 `source_type: local_scan` 和 `location: /hdd1/test_scan/xxx`
- **依赖**: Ollama 正常运行，embedding 模型可用

---

### 5. test_enrichment_integration.py — enrichment 集成测试

#### `TestEnrichmentIntegration`
- **功能**: 验证 local_scan 文件的 enrichment 功能
- **测试内容**:
  - 验证 retrieval_test 返回的 doc_aggs 包含 `source_type` 和 `location`
  - 验证 retrieval_test 返回的 chunks 包含 `source_type` 和 `location`
  - 验证聊天对话 references 包含 enrichment 字段
- **关键字段**:
  - `source_type`: 文件来源类型（如 `local_scan`）
  - `location`: 文件完整路径（如 `/hdd1/test_scan/2014胆囊.jpg`）

---

### 6. test_retrieval_source_type.py — 检索结果 source_type 测试

#### `TestRetrievalSourceType`
- **功能**: 验证检索结果正确包含 source_type 和 location
- **测试方法**:
  1. 创建 KB 并扫描路径
  2. 等待解析完成
  3. 调用 `/v1/chunk/retrieval_test`
  4. 验证返回的 doc_aggs 和 chunks 包含必需字段
- **验证字段**: `doc_id`, `doc_name`, `source_type`, `location`

---

### 7. test_video_ollama.py — Ollama VLM 视频帧解析

#### `test_single_video_parse`（参数化 × 4 视频）
- **功能**: 单次解析：提取帧 → 送入 VLM → 验证非空响应
- **方法**:
  1. 用 OpenCV 从视频提取 8 帧并缩放到最大 480px
  2. 构建 messages 发送给 Ollama `qwen3-vl:8b`
  3. 验证 VLM 返回非空内容
- **参数化**: 4 个视频 × 4 个预期关键词

#### `test_video_stability_5_runs`（参数化 × 4 视频）
- **功能**: 稳定性测试：同一视频跑 5 次
- **预期**: 5 次全部成功，无空响应

---

### 8. test_video_chunk.py — rag.app.picture.chunk 解析

#### `test_video_chunk`（参数化 × 4 视频）
- **功能**: 测试 RAGFlow 核心 `rag.app.picture.chunk` 函数解析视频
- **注意**: 此测试需要完整的 RAGFlow 后端环境，建议在 Docker 容器内运行：

```bash
docker exec -e PYTHONPATH=/ragflow:/tmp/testcases \
           docker-ragflow-cpu-1 \
           /ragflow/.venv/bin/python3 -m pytest \
           /tmp/testcases/test_http_api/test_scan_local_directory/test_video_chunk.py -v
```

---

## Enrichment 功能说明

### 功能描述
local_scan 文件（扫描路径添加的文件）在检索和聊天时需要返回 `source_type` 和 `location` 字段，以便前端正确显示文件链接。

### 后端修改
1. **api/db/services/dialog_service.py**:
   - 添加 `DocumentService` 导入
   - 在 `async_chat` 函数中添加 enrichment 代码（lines 633-648）
   - 在 `use_sql` 函数中添加 `enrich_references` helper 并调用（lines 813-838, 1243, 1261）

2. **rag/prompts/generator.py**:
   - `chunks_format()` 函数保留 `source_type` 和 `location` 字段

3. **api/apps/chunk_app.py**:
   - retrieval_test 接口返回的 doc_aggs 包含 enrichment 字段

### 前端修改
- `web/src/utils/local-scan-doc.ts`: 新增 `buildLocalScanDocUrl()` 工具函数
- `web/src/interfaces/database/chat.ts`: `Docagg` 接口添加 `source_type?` 和 `location?` 字段
- 多个 UI 组件更新为 local_scan 文件打开原文件而非缩略图

### API 响应格式
检索接口 (`/v1/chunk/retrieval_test`) 返回:
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
| `ollama_client` | session | Ollama Python 客户端（懒加载） |
| `set_tenant_info` | session (autouse) | 空 fixture，防止父 conftest 自动设置 tenant |
| `configure_ollama_img2txt` | module | 自动配置 Ollama image2text 模型 |

## 共享辅助函数

| 函数 | 说明 |
|---|---|
| `scan_path(auth, kb_id, path, scan_interval)` | POST `/v1/document/scan_path` |
| `list_documents(auth, kb_id)` | GET `/v1/document` |
| `get_scanned_directories(auth, kb_id)` | GET `/v1/document/scanned_directories` |
| `retrieval_test(auth, kb_id, question, ...)` | POST `/v1/chunk/retrieval_test` |

---

## 已知限制

1. **test_video_chunk** 在宿主机上无法运行（命名空间冲突）。需要完整 RAGFlow 后端环境。
2. **稳定性测试**（5 次）耗时约 65 秒/视频，CI 环境中可酌情跳过。
3. 聊天测试需要 Ollama embedding 模型可用，否则向量检索可能返回空结果。
4. 测试文件路径 `/hdd1/test_scan/` 必须在服务器上存在。
