# Agent Delegation Rules

## Subagent 使用规则
1. 提供完整上下文和相关文件
2. 明确目标和交付物
3. 限定范围 (不应该做什么)
4. 定义返回条件
5. 不允许级联 (subagent 不应再创建 subagent)

## Agent Teams 使用规则
1. Teammates 各自独立上下文
2. 限制每个 teammate 的 MCP 工具
3. 避免多个 teammate 修改同一文件
4. Lead 在关键节点必须 cunzhi

## 反模式
- 不委派简单任务 (overhead 不值得)
- 不在无上下文时委派
- 不让 subagent 修改关键配置文件
