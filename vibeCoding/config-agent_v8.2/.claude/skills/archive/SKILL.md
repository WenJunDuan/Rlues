---
name: archive
---

# 归档与上下文管理

## 工具

| 工具 | 类型 | 用法 | 调用方式 |
|:---|:---|:---|:---|
| sou | MCP | 语义搜索替代全文件加载 | `sou.search("关键词")` |
| skill/agent-teams | VibeCoding Skill | 800K+ 时拆分任务 | 加载 skill |

## 触发条件

Rev 阶段自动检查上下文使用量。riper-7.md Rev 调度。

## 上下文阈值策略

| 区间 | 策略 | 动作 |
|:---|:---|:---|
| 0-200K | 正常工作 | — |
| 200K-500K | 主动归档 | done.md 已验证 → archive.md |
| 500K-800K | 精准检索 | sou.search() 替代全文件读取 |
| 800K+ | 拆分 | 加载 skill/agent-teams |

## 归档流程

```
RIPER Rev 完成后:
  1. done.md 已验证任务 → archive.md
  2. 清理 doing.md
  3. 经验已提取到 .knowledge/ (不丢失)
```
