# SDK Layer

`adapter/sdk` 负责 Claude 官方 Python SDK 调用。

- SDK 依赖声明：`claude-agent-sdk==0.1.41`
- 安装命令：`python3 -m pip install --upgrade claude-agent-sdk==0.1.41`

- `runtime.py`: 加载 `claude-agent-sdk`（官方）
- `bridge.py`: 任务级 prompt 构造、查询、结果映射、超时处理
- `access.py`: SDK 权限策略读取（来自 `adapter/gateway/http_access.json` 的 `sdk` 段）

当前业务域仅支持 `/audit`。
