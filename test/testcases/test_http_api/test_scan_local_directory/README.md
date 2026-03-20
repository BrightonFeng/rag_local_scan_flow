# local_scan 测试用例说明

## 测试目录

```
test/testcases/test_http_api/test_scan_local_directory/
├── conftest.py              # 共享 fixtures 和辅助函数
├── video_utils.py           # 视频帧提取工具和测试数据定义
├── test_scan_path.py        # 扫描路径基础功能测试
├── test_ollama_setup.py     # Ollama LLM 配置测试
├── test_mp4_parsing.py     # MP4 视频端到端解析测试
├── test_video_ollama.py     # Ollama VLM 视频帧解析测试
└── test_video_chunk.py      # rag.app.picture.chunk 视频解析测试
```

## 快速运行

```bash
# 运行所有测试（需设置 ZHIPU_AI_API_KEY）
ZHIPU_AI_API_KEY=dummy pytest test/testcases/test_http_api/test_scan_local_directory/ -v

# 运行指定测试文件
ZHIPU_AI_API_KEY=dummy pytest test/testcases/test_http_api/test_scan_local_directory/test_ollama_setup.py -v

# 运行单个测试
ZHIPU_AI_API_KEY=dummy pytest "test/testcases/test_http_api/test_scan_local_directory/test_video_ollama.py::TestVideoOllamaParsing::test_single_video_parse" -v
```

## 依赖条件

### 环境依赖
| 依赖 | 说明 |
|---|---|
| RAGFlow API | `http://127.0.0.1:9380` |
| Ollama 服务 | `http://localhost:11434`（需包含 `qwen3-vl:8b` 模型） |
| 测试视频文件 | `/hdd1/test_scan/test1/*.mp4`（见下方说明） |
| ZHIPU_AI_API_KEY | 环境变量（可用 dummy 值绕过） |

### 测试视频文件
测试使用 4 个视频文件，通过符号链接存放于 `/hdd1/test_scan/test1/`：

```bash
# 创建目录和符号链接（首次设置）
mkdir -p /hdd1/test_scan/test1
ln -sf "/hdd1/photo/20/澳大利亚/VID_20200126_091125.mp4" "/hdd1/test_scan/test1/091125.mp4"
ln -sf "/hdd1/photo/20/澳大利亚/VID_20200126_100305.mp4" "/hdd1/test_scan/test1/100305.mp4"
ln -sf "/hdd1/photo/20/澳大利亚/海狮1.mp4" "/hdd1/test_scan/test1/海狮1.mp4"
ln -sf "/hdd1/video/自拍精选/2018/骑马.mp4" "/hdd1/test_scan/test1/骑马.mp4"
```

### Python 依赖
| 包 | 说明 |
|---|---|
| pytest | 测试框架 |
| requests | HTTP 调用 |
| ollama | Ollama API 客户端 |
| opencv-python-headless | 视频帧提取 |
| ragflow 完整依赖 | 仅 `test_video_chunk` 需要 |

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
- **方法**: 用 `HttpApiAuth` + `add_dataset` 调用 `/v1/document/scan_path`，路径为 `/nonexistent/path/12345`
- **预期**: 返回非 0 code
- **依赖**: `HttpApiAuth`, `add_dataset` fixture

---

### 2. test_ollama_setup.py — Ollama LLM 配置

#### `test_set_ollama_api_key`
- **功能**: 配置 Ollama 作为 LLM Provider（设置 API Key）
- **方法**: POST `/v1/llm/set_api_key`，api_key 为空（Ollama 不需要）
- **预期**: HTTP 200
- **依赖**: `scan_auth` fixture
- **运行时间**: < 5 秒

#### `test_list_ollama_models`
- **功能**: 验证 Ollama 模型列表可正确获取
- **方法**: GET `/v1/llm/list`
- **预期**: 返回数据中包含 "Ollama" factory，且有可用模型
- **依赖**: `scan_auth` fixture
- **运行时间**: < 5 秒

#### `test_set_tenant_models_for_ollama`
- **功能**: 将租户的 LLM / Embedding / Image2Text 模型切换为 Ollama
- **方法**: 获取 Ollama 模型列表 → 获取租户信息 → POST `/v1/user/set_tenant_info`
- **预期**: 设置成功，返回 code 0
- **依赖**: `scan_auth` fixture，且 Ollama 服务必须运行并包含 chat/embedding/image2text 模型
- **运行时间**: < 10 秒

---

### 3. test_mp4_parsing.py — MP4 端到端解析

#### `test_scan_video_directory_and_wait`
- **功能**: 创建知识库 → 扫描视频目录 → 等待解析完成 → 验证状态
- **方法**:
  1. POST `/v1/kb/create` 创建临时 KB
  2. POST `/v1/document/scan_path` 扫描 `/hdd1/test_scan/test1`（含 4 个视频）
  3. 轮询（最多 120 秒）GET `/v1/document/list` 检查文档解析状态
  4. 清理：DELETE `/v1/kb/{kb_id}`
- **预期**: 所有文档状态为 `success`，无 `failed` 状态
- **依赖**: `scan_auth` fixture；Ollama 正常运行；视频文件存在
- **运行时间**: ~120 秒（最多等待 120 秒视频解析）

---

### 4. test_video_ollama.py — Ollama VLM 视频帧解析

视频帧提取参数：最大尺寸 480px，提取 8 帧，JPEG 质量 85

#### `test_single_video_parse`（参数化 × 4 视频）
- **功能**: 单次解析：提取帧 → 送入 VLM → 验证非空响应
- **方法**:
  1. 用 OpenCV 从视频提取 8 帧并缩放到最大 480px
  2. 构建 messages（中文描述请求）发送给 Ollama `qwen3-vl:8b`
  3. 验证 VLM 返回非空内容
- **参数化**: 4 个视频 × 4 个预期关键词
  | 视频文件 | 预期关键词 |
  |---|---|
  | `091125.mp4` | koala（树袋熊） |
  | `100305.mp4` | lizard（蜥蜴） |
  | `海狮1.mp4` | sea lion（海狮） |
  | `骑马.mp4` | horse（马） |
- **预期**: VLM 返回内容非空，帧大小 < 200KB/帧
- **依赖**: `ollama_client` fixture；`qwen3-vl:8b` 模型
- **运行时间**: ~15 秒/视频

#### `test_video_stability_10_runs`（参数化 × 4 视频）
- **功能**: 稳定性测试：同一视频跑 10 次，验证无空响应或重复输出
- **方法**: 对每个视频重复 10 次 `test_single_video_parse` 逻辑
- **预期**: 10 次全部成功，无空响应，无明显重复（唯一词比例 > 30%）
- **依赖**: 同 `test_single_video_parse`
- **运行时间**: ~135 秒/视频（10 × ~13.5 秒）

---

### 5. test_video_chunk.py — rag.app.picture.chunk 解析

#### `test_video_chunk`（参数化 × 4 视频）
- **功能**: 测试 RAGFlow 核心 `rag.app.picture.chunk` 函数解析视频
- **方法**:
  1. 读取视频文件字节
  2. 调用 `rag.app.picture.chunk(filename, video_bytes, tenant_id, language, callback)`
  3. 验证返回非空
- **预期**: chunk 函数返回有效解析结果
- **依赖**: `rag` 完整后端（rag/、api/、deepdoc/、common/ 等挂载）；RAGFlow 数据库连接；Ollama 正常运行
- **运行时间**: ~20-60 秒/视频（取决于视频长度）
- **注意**: 此测试需要完整的 RAGFlow 后端环境，在宿主机直接运行会因 `rag.common` vs `testcases.common` 命名空间冲突而失败。**建议在 Docker 容器内运行**：
  ```bash
  # 在 Docker 内运行（需 PYTHONPATH 设置正确）
  docker exec -e PYTHONPATH=/ragflow:/tmp/testcases \
             -e ZHIPU_AI_API_KEY=dummy \
             docker-ragflow-cpu-1 \
             /ragflow/.venv/bin/python3 -m pytest \
             /tmp/testcases/test_http_api/test_scan_local_directory/test_video_chunk.py -v
  ```

---

## 共享 Fixtures（conftest.py）

| Fixture | Scope | 说明 |
|---|---|---|
| `scan_auth` | session | 登录获取 Authorization header |
| `ollama_client` | session | Ollama Python 客户端（懒加载） |
| `set_tenant_info` | session (autouse) | 空 fixture，防止父 conftest 自动设置 tenant |

## 共享辅助函数

| 函数 | 说明 |
|---|---|
| `scan_path(auth, kb_id, path, scan_interval)` | POST `/v1/document/scan_path` |
| `list_documents(auth, kb_id)` | GET `/v1/document` |
| `get_scanned_directories(auth, kb_id)` | GET `/v1/document/scanned_directories` |
| `update_scan_interval(auth, dir_id, scan_interval)` | PUT `/v1/document/scanned_directories/{id}` |
| `retrieval_test(auth, kb_id, question, ...)` | POST `/v1/chunk/retrieval_test` |

## 父级 Fixtures（由 `testcases/conftest.py` 和 `test_http_api/conftest.py` 提供）

| Fixture | Scope | 说明 |
|---|---|---|
| `HttpApiAuth` | session | `RAGFlowHttpApiAuth` 认证对象 |
| `add_dataset` | class | 创建临时 KB，测试结束后清理 |
| `clear_datasets` | session | 测试前清空所有 KB |
| `auth` | session | 原始 token |
| `token` | session | 从 `/v1/system/new_token` 获取 |

---

## 已知限制

1. **test_video_chunk** 在宿主机上无法运行（命名空间冲突）。需要完整 RAGFlow 后端环境。
2. **稳定性测试**（10 次）耗时较长（约 135 秒/视频），CI 环境中可酌情跳过。
3. 测试视频文件通过符号链接存放，首次使用需手动创建链接。
4. 某些测试需要有效的 KB（由 `add_dataset` fixture 提供），当前 tenant 环境隔离问题可能导致部分依赖 KB 的测试失败。
