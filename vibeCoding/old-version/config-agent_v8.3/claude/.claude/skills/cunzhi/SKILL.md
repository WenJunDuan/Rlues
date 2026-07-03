---
name: cunzhi
description: 人工确认检查点协议 — 关键决策前暂停等待人工确认, 使用 MCP cunzhi 工具
context: main
---

# 寸止 — 人工确认检查点

## 核心原则

寸止 = 在关键节点**真正暂停**, 等待人工确认后才继续。
不是形式化的"确认一下", 是真正的决策门控。

## 触发条件

### 必须检查点 (●)
- `DESIGN_READY`: 设计方案确定前
- `PLAN_APPROVED`: 任务拆解确认前
- `REVIEW_DONE`: 代码审查完成, 准备交付前
- Path 升级时 (如 B → C)

### 条件检查点 (○)
- R 阶段 Path C+: 研究充分性确认
- E 阶段大规模修改: >100 行或 >3 文件
- V 阶段累计失败 ≥ 3 次

## MCP 调用协议

```
1. 准备 cunzhi 摘要:
   - 当前阶段 + Path
   - 关键决策/发现
   - 需要确认的具体问题

2. 调用 MCP cunzhi:
   message: "[阶段] 检查点摘要..."

3. 等待响应:
   - 确认 → 继续下一步
   - 修改 → 按反馈调整后重新提交
   - 拒绝 → 回退到上一阶段

4. 记录到 .ai_state:
   checkpoint: DESIGN_READY
   result: approved/modified/rejected
   timestamp: {ISO}
```

## 不可降级

cunzhi 是 VibeCoding 的硬约束。
MCP 不可用 → 用 `input()` / 对话确认替代, 但不可跳过。
自动确认 = 违反铁律第 3 条。
