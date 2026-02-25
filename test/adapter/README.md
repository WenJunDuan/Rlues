# Adapter Gateway

`adapter` 已按分层重构：

- `adapter/gateway/`：HTTP 网关层（路由、鉴权、暴露策略）
- `adapter/core/`：任务队列、状态存储、日志与结果查询
- `adapter/sdk/`：Claude SDK 运行时加载、权限策略、桥接调用

当前只保留一个业务域：`/audit`（报销审核）。

## Install

```bash
python3 -m pip install fastapi uvicorn
python3 -m pip install --upgrade claude-agent-sdk==0.1.41
```

## Run

推荐新入口：

```bash
uvicorn adapter.gateway.http_server:create_app --factory --host 0.0.0.0 --port 8000
```

## Active Endpoints

- `GET /health`
- `POST /api/audit`
- `POST /api/audit/review`
- `GET /api/task/{task_id}`
- `GET /api/task/{task_id}/events`
- `GET /api/task/{task_id}/compliance`
- `GET /api/audit/{task_id}`
- `GET /api/audit/{task_id}/events`
- `GET /api/audit/{task_id}/compliance`
- `GET /api/history` (internal)
- `DELETE /api/history/{task_id}` (internal)
- `GET /api/logs` (internal)
- `POST /api/logs/archive` (internal)
- `GET /api/runtime/queue` (internal)
- `GET /api/runtime/exposure` (internal)

兼容 legacy（默认关闭）：

- `POST /task`
- `GET /task/{task_id}`
- `GET /task/{task_id}/events`
- `GET /task/{task_id}/compliance`

## Gateway Config

网关策略文件：`adapter/gateway/http_access.json`

- `features`: 当前仅 `audit`
- `endpoints`: endpoint 级开关 + `public/internal` scope
- `auth.header`: 默认 `X-Adapter-Key`
- `auth.public_api_keys` / `auth.internal_api_keys`
- `sdk`: SDK 调用权限策略（`permission_mode/sandbox/allowed_tools/...`）

### Auth Defaults (Hardened)

- `public_api_keys` 和 `internal_api_keys` 任一缺失都会导致对应 scope 请求被拒绝。
- 公共接口必须带 `X-Adapter-Key`。
- 内部接口必须使用 `internal_api_keys` 中的 key。
- 默认配置不再内置示例 key，请在配置文件或环境变量显式设置。

### Caller Context Headers

- 提交与查询报销任务时，需要传：
  - `X-Tenant-Id`
  - `X-Operator-Id`
- 提交阶段会校验上述 header 与 `payload.context` 一致。
- 查询阶段会校验 header 与任务归属一致，且绑定提交时的 API key（内部 key 可跨任务诊断）。

可用环境变量：

- `ADAPTER_HTTP_ACCESS_CONFIG`
- `ADAPTER_PUBLIC_API_KEYS`
- `ADAPTER_INTERNAL_API_KEYS`
- `ADAPTER_SDK_SETTING_SOURCES`
- `ADAPTER_SDK_PERMISSION_MODE`
- `ADAPTER_SDK_SANDBOX`
- `ADAPTER_SDK_ALLOWED_TOOLS`
- `ADAPTER_SDK_ENABLE_PLUGIN_BASH`

## Runtime Files

- 运行日志：`.ai_state/logs/adapter.log`
- 任务历史：`.ai_state/logs/task_history.jsonl`
- 状态快照：`.ai_state/state/adapter_state.json`

可覆盖：

- `ADAPTER_LOG_DIR`
- `ADAPTER_STATE_DIR`
- `ADAPTER_HISTORY_MAX_BYTES`
- `ADAPTER_HISTORY_BACKUP_COUNT`
