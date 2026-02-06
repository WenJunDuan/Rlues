# Performance Rules

## effort 选择

| 任务 | effort | 原因 |
|:---|:---|:---|
| 快速编辑 | low | 极速响应 |
| 功能实现 | medium/high | 平衡质量和速度 |
| 架构决策 | max | 需要深度推理 |

## 上下文管理 (1M 时代)

| 使用量 | 动作 |
|:---|:---|
| 0-200K | 正常 |
| 200K-500K | 监控 |
| 500K-800K | smart-archive 触发 |
| 800K+ | 建议 Agent Teams |

## MCP 优化
- 不同时启用所有 MCP
- 总工具数 <80
- 用 disabledMcpServers 禁用未使用的

## Token 优化
- 优先 skills 而非冗长 prompt
- 按需加载知识
- 使用 iterative-retrieval 分批检索
