---
name: cunzhi
description: "Checkpoint-based pause and confirm system using cunzhi MCP for quality gates"
---

# 寸止 (Cunzhi)

真暂停 + 等待确认。不是输出"请确认"然后继续。

## 工具

| 工具 | 类型 | 用法 | 调用方式 |
|:---|:---|:---|:---|
| cunzhi MCP | MCP | 真暂停等待用户 | `cunzhi.confirm({ checkpoint, summary, options })` |

## 调用方式

```javascript
cunzhi.confirm({
  checkpoint: "PLAN_READY",
  summary: "方案概要...",
  options: ["确认", "修改", "取消"]
})
```

## 检查点清单

| 检查点 | RIPER 阶段 | Path | 触发条件 |
|:---|:---|:---|:---|
| DESIGN_READY | D 完成 | B/C/D | 方案选定 |
| PLAN_READY | P 完成 | B/C/D | 任务拆解完 |
| CONFIRMED | C 完成 | B/C/D | 验收标准确认 |
| PHASE_DONE | E 中间 | C | 九步各阶段 |
| TEAM_PLAN | E 分配前 | D | Teams 任务分配 |
| TEAM_DONE | E 合并后 | D | Teams 全完成 |
| VERIFIED | V 通过 | C/D | 验证通过 |
| VERIFY_FAIL | V 失败 | All | 3 次验证失败 |
| TASK_DONE | Rev 完成 | All | 任务归档 |

## 降级

MCP 不可用 → 输出 `[CUNZHI checkpoint_name]` 文字标记 + 等待用户回复。
永不跳过。
