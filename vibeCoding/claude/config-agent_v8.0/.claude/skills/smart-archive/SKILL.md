---
name: smart-archive
description: |
  Intelligent context archiving for the 1M token era.
  Replaces strategic-compact. Works with server-side Compaction API.
  Archives completed RIPER phases to .ai_state/ instead of emergency compression.
---

# Smart Archive Skill (was: strategic-compact)

## v8.0 变更

旧策略 (200K): 紧急压缩，丢失上下文
新策略 (1M): 智能归档，配合服务端 Compaction

## 上下文层级策略

| 使用量 | 动作 |
|:---|:---|
| 0-200K | 正常工作，无干预 |
| 200K-500K | 监控。服务端 Compaction 自动启用 |
| 500K-800K | 主动归档已完成阶段到 .ai_state/ |
| 800K+ | 建议拆分为 Agent Teams (Path D) |

## 归档策略

已完成的 RIPER 阶段上下文 → 摘要写入 .ai_state/archive.md：

```markdown
### Archive: R1 Research Phase - {{timestamp}}
- 搜索范围: {{files}}
- 关键发现: {{findings}}
- 决策: {{decisions}}
```

只保留关键信息，删除搜索结果原文等低密度内容。

## 与 Compaction API 配合

服务端 Compaction 自动压缩旧消息。
smart-archive 的价值在于：在 Compaction 之前，确保关键决策和上下文已持久化到 .ai_state/。

```
关键信息 → .ai_state/ (永久)
会话上下文 → Compaction 处理 (自动摘要)
```
