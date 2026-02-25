# Gateway Layer

网关层负责三件事：

1. 接收 HTTP 请求并做鉴权/暴露策略检查
2. 把请求标准化成 `TaskEnvelope` 并投递到 `core` 队列
3. 提供任务查询、历史查询、日志查询与运行时诊断接口

## Files

- `adapter/gateway/http_server.py`
  - FastAPI 路由入口
  - endpoint 级 access guard
  - HTTP status 映射
- `adapter/gateway/http_access.py`
  - feature + endpoint + key scope 策略加载
  - env 覆盖与脱敏导出
- `adapter/gateway/http_access.json`
  - 当前运行配置（仅 `audit`）

## HTTP -> SDK 调度链

`POST /api/audit(/review)`
-> `gateway.http_server._submit_feature_command()`
-> `core.api_server.submit_task()`
-> `core` 队列线程调度
-> `sdk.bridge.execute_task()`
-> `sdk.runtime.load_claude_sdk_runtime()`
-> `claude_agent_sdk.query()`

## 关键设计

- 同 `tenant_id:operator_id` 串行
- 跨会话并发受 `max_concurrent_sessions` 限制
- 请求与执行解耦：提交返回 `202`，结果轮询查询
- 内部接口通过 `scope=internal` + key 控制
- 任务提交/查询绑定归属：`X-Tenant-Id` + `X-Operator-Id`
- 查询阶段要求归属匹配且校验提交时 API key 指纹（内部 key 可用于运维诊断）
