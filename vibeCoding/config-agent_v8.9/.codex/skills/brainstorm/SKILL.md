---
name: brainstorm
description: 苏格拉底式需求精炼 — R₀b 阶段
---
## 触发
Path B+ 任务启动时, RIPER R₀b 阶段。

## 工具
| 工具 | 类型 | 调用方式 |
|:---|:---|:---|
| augment-context-engine | MCP | 搜索现有代码 |
| mcp-deepwiki | MCP | 查候选库文档 |
| cunzhi | MCP | [DESIGN_DIRECTION] 确认 |

## 流程
1. augment-context-engine 搜索项目关键文件
2. 读 .ai_state/conventions.md 和 .knowledge/pitfalls.md
3. 逐个提问 (一次一问, 优先选择题, YAGNI)
4. 提出 2-3 方案, deepwiki 验证可行性
5. 分段呈现 (≤200 字/段, 逐段确认)
6. 输出 .ai_state/design.md
7. cunzhi [DESIGN_DIRECTION]

## 降级
MCP 不可用 → 对话提问, 手动记录 design.md。
