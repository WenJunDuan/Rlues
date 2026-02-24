---
name: cunzhi
description: 人工确认检查点协议 — 关键决策前必须获得人工确认
context: main
---

# Cunzhi — 寸止检查点

## 检查点

| ID | 触发时机 | Path |
|:---|:---|:---|
| REQ_CONFIRMED | R₀ 需求理解确认 (R₀→R) | B+ |
| DESIGN_READY | 设计方案确定 (D→P) | B+ |
| PLAN_APPROVED | 任务列表确定 (P→E) | B+ |
| BIG_CHANGE | 修改 >100行 或 >3文件 | B+ |
| REVIEW_DONE | 审查通过 (Rev→A) | B+ |
| PATH_UPGRADE | 路径升级 | 全部 |
| FAIL_3X | T 阶段累计失败 ≥ 3 次 | 全部 |

## 交互格式

```
[cunzhi] {ID}
摘要: {一句话}
关键决策: {内容}
选项: [确认] [修改] [拒绝]
```

MCP 不可用 → 直接在对话中同格式请求确认。
